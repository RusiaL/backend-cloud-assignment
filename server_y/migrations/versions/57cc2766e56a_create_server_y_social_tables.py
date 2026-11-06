"""Create Server Y social tables

Revision ID: 57cc2766e56a
Revises:
Create Date: 2026-11-06
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "57cc2766e56a"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("comment_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="comments_pkey"),
    )

    op.create_table(
        "likes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="likes_pkey"),
        sa.UniqueConstraint(
            "user_id",
            "post_id",
            name="likes_user_id_post_id_key",
        ),
    )

    op.create_table(
        "reactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("reaction_type", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="reactions_pkey"),
        sa.UniqueConstraint(
            "user_id",
            "post_id",
            name="reactions_user_id_post_id_key",
        ),
    )


def downgrade():
    op.drop_table("reactions")
    op.drop_table("likes")
    op.drop_table("comments")