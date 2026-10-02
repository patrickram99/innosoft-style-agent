"""US-01: tabla manuscripts

Revision ID: 0001_manuscripts
Revises:
Create Date: 2026-10-02
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_manuscripts"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "manuscripts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("submission_id", sa.Integer(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("parent_id", sa.String(length=36), nullable=True),
        sa.Column("section_id", sa.Integer(), nullable=True),
        sa.Column("article_type", sa.String(length=16), nullable=True),
        sa.Column("locale", sa.String(length=16), nullable=True),
        sa.Column("language", sa.String(length=8), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="received"),
        sa.Column("status_reason", sa.String(length=64), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_manuscripts_submission_id", "manuscripts", ["submission_id"])
    op.create_index("ix_manuscripts_sha256", "manuscripts", ["sha256"])


def downgrade() -> None:
    op.drop_index("ix_manuscripts_sha256", table_name="manuscripts")
    op.drop_index("ix_manuscripts_submission_id", table_name="manuscripts")
    op.drop_table("manuscripts")
