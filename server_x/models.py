from datetime import datetime

from server_x.extensions import db

class Like(db.Model):
    __tablename__ = "likes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    post_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(
        db.DateTime,
        nullable=True,
        default=datetime.utcnow
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "post_id",
            name="likes_user_id_post_id_key"
        ),
    )


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    post_id = db.Column(db.Integer, nullable=False)
    comment_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime,
        nullable=True,
        default=datetime.utcnow
    )


class Reaction(db.Model):
    __tablename__ = "reactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    post_id = db.Column(db.Integer, nullable=False)
    reaction_type = db.Column(db.String, nullable=False)
    created_at = db.Column(
        db.DateTime,
        nullable=True,
        default=datetime.utcnow
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "post_id",
            name="reactions_user_id_post_id_key"
        ),
    )