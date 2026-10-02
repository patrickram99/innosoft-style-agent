"""US-04: tabla documents

Revision ID: 0002_documents
Revises: 0001_manuscripts
Create Date: 2026-10-02
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_documents"
down_revision = "0001_manuscripts"
branch_labels = None
depends_on = None

JSONB = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("manuscript_id", sa.String(length=36), sa.ForeignKey("manuscripts.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("page_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pages", JSONB, nullable=False),
        sa.Column("sections", JSONB, nullable=False),
        sa.Column("figures", JSONB, nullable=False),
        sa.Column("citations", JSONB, nullable=False),
        sa.Column("references", JSONB, nullable=False),
        sa.Column("extractor_version", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("documents")
