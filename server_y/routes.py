from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

from server_y.extensions import db
from server_y.models import Like, Comment, Reaction


bp = Blueprint("server_y", __name__)


def get_authenticated_user_id():
    try:
        return int(get_jwt_identity())
    except (TypeError, ValueError):
        return None


def check_user_access(user_id):
    authenticated_user_id = get_authenticated_user_id()

    if authenticated_user_id is None:
        return jsonify({"error": "Invalid user identity"}), 401

    if authenticated_user_id != user_id:
        return jsonify({"error": "Access denied"}), 403

    return None


def validate_post_id(data):
    post_id = data.get("post_id")

    if isinstance(post_id, bool) or not isinstance(post_id, int) or post_id <= 0:
        return None

    return post_id


@bp.route("/")
def home():
    return {
        "server": "Y",
        "status": "running"
    }


@bp.route("/internal/likes", methods=["POST"])
def internal_create_like():
    api_key = request.headers.get("X-API-Key")

    if api_key != current_app.config["SERVER_C_API_KEY"]:
        return {"error": "Unauthorized"}, 401

    data = request.get_json(silent=True) or {}

    user_id = data.get("user_id")
    post_id = validate_post_id(data)

    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
        return {"error": "Valid user_id is required"}, 400

    if post_id is None:
        return {"error": "Valid post_id is required"}, 400

    like = Like(user_id=user_id, post_id=post_id)

    try:
        db.session.add(like)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "Like already exists"}, 409

    return {
        "id": like.id,
        "user_id": like.user_id,
        "post_id": like.post_id
    }, 201


@bp.route("/likes", methods=["POST"])
@jwt_required()
def create_like():
    data = request.get_json(silent=True) or {}

    user_id = get_authenticated_user_id()
    post_id = validate_post_id(data)

    if user_id is None:
        return {"error": "Invalid user identity"}, 401

    if post_id is None:
        return {"error": "Valid post_id is required"}, 400

    like = Like(user_id=user_id, post_id=post_id)

    try:
        db.session.add(like)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "Like already exists"}, 409

    return {
        "id": like.id,
        "user_id": like.user_id,
        "post_id": like.post_id
    }, 201


@bp.route("/likes/<int:user_id>", methods=["GET"])
@jwt_required()
def get_likes(user_id):
    access_error = check_user_access(user_id)

    if access_error:
        return access_error

    likes = (
        Like.query
        .filter_by(user_id=user_id)
        .order_by(Like.created_at)
        .all()
    )

    return {
        "user_id": user_id,
        "likes": [
            {
                "id": like.id,
                "user_id": like.user_id,
                "post_id": like.post_id,
                "created_at": like.created_at.isoformat() if like.created_at else None
            }
            for like in likes
        ]
    }, 200


@bp.route("/comments", methods=["POST"])
@jwt_required()
def create_comment():
    data = request.get_json(silent=True) or {}

    user_id = get_authenticated_user_id()
    post_id = validate_post_id(data)
    comment_text = data.get("comment_text")

    if user_id is None:
        return {"error": "Invalid user identity"}, 401

    if post_id is None:
        return {"error": "Valid post_id is required"}, 400

    if not isinstance(comment_text, str) or not comment_text.strip():
        return {"error": "comment_text is required"}, 400

    comment = Comment(
        user_id=user_id,
        post_id=post_id,
        comment_text=comment_text.strip()
    )

    db.session.add(comment)
    db.session.commit()

    return {
        "id": comment.id,
        "user_id": comment.user_id,
        "post_id": comment.post_id,
        "comment_text": comment.comment_text
    }, 201


@bp.route("/comments/<int:user_id>", methods=["GET"])
@jwt_required()
def get_comments(user_id):
    access_error = check_user_access(user_id)

    if access_error:
        return access_error

    comments = (
        Comment.query
        .filter_by(user_id=user_id)
        .order_by(Comment.created_at)
        .all()
    )

    return {
        "user_id": user_id,
        "comments": [
            {
                "id": comment.id,
                "user_id": comment.user_id,
                "post_id": comment.post_id,
                "comment_text": comment.comment_text,
                "created_at": comment.created_at.isoformat() if comment.created_at else None
            }
            for comment in comments
        ]
    }, 200


@bp.route("/reactions", methods=["POST"])
@jwt_required()
def create_reaction():
    data = request.get_json(silent=True) or {}

    user_id = get_authenticated_user_id()
    post_id = validate_post_id(data)
    reaction_type = data.get("reaction_type")

    if user_id is None:
        return {"error": "Invalid user identity"}, 401

    if post_id is None:
        return {"error": "Valid post_id is required"}, 400

    if not isinstance(reaction_type, str) or not reaction_type.strip():
        return {"error": "reaction_type is required"}, 400

    reaction = Reaction(
        user_id=user_id,
        post_id=post_id,
        reaction_type=reaction_type.strip()
    )

    try:
        db.session.add(reaction)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "Reaction already exists"}, 409

    return {
        "id": reaction.id,
        "user_id": reaction.user_id,
        "post_id": reaction.post_id,
        "reaction_type": reaction.reaction_type
    }, 201


@bp.route("/reactions/<int:user_id>", methods=["GET"])
@jwt_required()
def get_reactions(user_id):
    access_error = check_user_access(user_id)

    if access_error:
        return access_error

    reactions = (
        Reaction.query
        .filter_by(user_id=user_id)
        .order_by(Reaction.created_at)
        .all()
    )

    return {
        "user_id": user_id,
        "reactions": [
            {
                "id": reaction.id,
                "user_id": reaction.user_id,
                "post_id": reaction.post_id,
                "reaction_type": reaction.reaction_type,
                "created_at": reaction.created_at.isoformat() if reaction.created_at else None
            }
            for reaction in reactions
        ]
    }, 200