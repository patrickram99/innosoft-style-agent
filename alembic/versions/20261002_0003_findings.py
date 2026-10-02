"""US-10: tabla findings y columna documents.rule_errors

Revision ID: 0003_findings
Revises: 0002_documents
Create Date: 2026-10-02
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_findings"
down_revision = "0002_documents"
branch_labels = None
depends_on = None

JSONB = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "findings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("manuscript_id", sa.String(length=36), sa.ForeignKey("manuscripts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=True),
        sa.Column("rule_id", sa.String(length=8), nullable=False),
        sa.Column("severidad", sa.String(length=8), nullable=False),
        sa.Column("pagina", sa.Integer(), nullable=True),
        sa.Column("ubicacion", JSONB, nullable=False),
        sa.Column("evidencia", JSONB, nullable=False),
        sa.Column("valor_encontrado", sa.Text(), nullable=True),
        sa.Column("valor_esperado", sa.Text(), nullable=True),
        sa.Column("requires_llm", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_findings_manuscript_id", "findings", ["manuscript_id"])
    op.create_index("ix_findings_rule_id", "findings", ["rule_id"])
    # Hasta que exista la tabla runs (US-28), los rule_error de un análisis se guardan en el documento.
    with op.batch_alter_table("documents") as batch:
        batch.add_column(sa.Column("rule_errors", JSONB, nullable=True))
        batch.add_column(sa.Column("rules_hash", sa.String(length=64), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("documents") as batch:
        batch.drop_column("rules_hash")
        batch.drop_column("rule_errors")
    op.drop_index("ix_findings_rule_id", table_name="findings")
    op.drop_index("ix_findings_manuscript_id", table_name="findings")
    op.drop_table("findings")
