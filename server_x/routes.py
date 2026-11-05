import requests
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

from server_x.extensions import db
from server_x.models import Like, Comment, Reaction


bp = Blueprint("social", __name__)


def get_authenticated_user_id():
    """Get the user ID from the validated JWT."""
    try:
        return int(get_jwt_identity())
    except (TypeError, ValueError):
        return None


def check_user_access(user_id):
    """Ensure users can access only their own records."""
    authenticated_user_id = get_authenticated_user_id()

    if authenticated_user_id is None:
        return jsonify({"error": "Invalid user identity in token"}), 401

    if authenticated_user_id != user_id:
        return jsonify({"error": "Access denied"}), 403

    return None


def validate_post_id(data):
    post_id = data.get("post_id")

    if not isinstance(post_id, int) or isinstance(post_id, bool) or post_id <= 0:
        return None

    return post_id


# --------------------
# LIKES
# --------------------

@bp.route("/likes", methods=["POST"])
@jwt_required()
def create_like():
    data = request.get_json(silent=True) or {}
    post_id = validate_post_id(data)
    user_id = get_authenticated_user_id()

    if post_id is None:
        return jsonify({"error": "A valid post_id is required"}), 400

    if user_id is None:
        return jsonify({"error": "Invalid user identity in token"}), 401

    like = Like(user_id=user_id, post_id=post_id)

    try:
        db.session.add(like)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Like already exists"}), 409

    return jsonify({
        "id": like.id,
        "user_id": like.user_id,
        "post_id": like.post_id
    }), 201


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

    return jsonify({
        "user_id": user_id,
        "likes": [
            {
                "id": like.id,
                "user_id": like.user_id,
                "post_id": like.post_id,
                "created_at": (
                    like.created_at.isoformat()
                    if like.created_at else None
                )
            }
            for like in likes
        ]
    }), 200


# --------------------
# COMMENTS
# --------------------

@bp.route("/comments", methods=["POST"])
@jwt_required()
def create_comment():
    data = request.get_json(silent=True) or {}
    post_id = validate_post_id(data)
    comment_text = data.get("comment_text")
    user_id = get_authenticated_user_id()

    if post_id is None:
        return jsonify({"error": "A valid post_id is required"}), 400

    if not isinstance(comment_text, str) or not comment_text.strip():
        return jsonify({"error": "A non-empty comment_text is required"}), 400

    if user_id is None:
        return jsonify({"error": "Invalid user identity in token"}), 401

    comment = Comment(
        user_id=user_id,
        post_id=post_id,
        comment_text=comment_text.strip()
    )

    db.session.add(comment)
    db.session.commit()

    return jsonify({
        "id": comment.id,
        "user_id": comment.user_id,
        "post_id": comment.post_id,
        "comment_text": comment.comment_text
    }), 201


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

    return jsonify({
        "user_id": user_id,
        "comments": [
            {
                "id": comment.id,
                "user_id": comment.user_id,
                "post_id": comment.post_id,
                "comment_text": comment.comment_text,
                "created_at": (
                    comment.created_at.isoformat()
                    if comment.created_at else None
                )
            }
            for comment in comments
        ]
    }), 200


# --------------------
# REACTIONS
# --------------------

@bp.route("/reactions", methods=["POST"])
@jwt_required()
def create_reaction():
    data = request.get_json(silent=True) or {}
    post_id = validate_post_id(data)
    reaction_type = data.get("reaction_type")
    user_id = get_authenticated_user_id()

    if post_id is None:
        return jsonify({"error": "A valid post_id is required"}), 400

    if not isinstance(reaction_type, str) or not reaction_type.strip():
        return jsonify({"error": "A non-empty reaction_type is required"}), 400

    if user_id is None:
        return jsonify({"error": "Invalid user identity in token"}), 401

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
        return jsonify({"error": "Reaction already exists for this post"}), 409

    return jsonify({
        "id": reaction.id,
        "user_id": reaction.user_id,
        "post_id": reaction.post_id,
        "reaction_type": reaction.reaction_type
    }), 201


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

    return jsonify({
        "user_id": user_id,
        "reactions": [
            {
                "id": reaction.id,
                "user_id": reaction.user_id,
                "post_id": reaction.post_id,
                "reaction_type": reaction.reaction_type,
                "created_at": (
                    reaction.created_at.isoformat()
                    if reaction.created_at else None
                )
            }
            for reaction in reactions
        ]
    }), 200

@bp.route("/sync/likes", methods=["POST"])
def sync_likes():
    api_key = request.headers.get("X-API-Key")

    expected_api_key = current_app.config.get("SERVER_C_API_KEY")

    if not expected_api_key or api_key != expected_api_key:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body"}), 400

    server_c_url = current_app.config.get("SERVER_C_URL")

    if not server_c_url:
        return jsonify({"error": "Server C URL is not configured"}), 500

    try:
        response = requests.post(
            f"{server_c_url.rstrip('/')}/sync/likes",
            headers={"X-API-Key": expected_api_key},
            json=data,
            timeout=10
        )

        try:
            response_data = response.json()
        except ValueError:
            response_data = {"error": "Invalid response from Server C"}

        return jsonify(response_data), response.status_code

    except requests.RequestException:
        current_app.logger.exception("Failed to contact Server C")
        return jsonify({"error": "Server C is unavailable"}), 502