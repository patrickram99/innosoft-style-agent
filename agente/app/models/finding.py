"""Finding model (US-10): one detected non-compliance, traceable to a rule_id (RNF-04)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import JSONVariant
from app.models.base import Base
from app.models.manuscript import new_uuid, utcnow


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    manuscript_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("manuscripts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    run_id: Mapped[str | None] = mapped_column(String(36), nullable=True)  # US-28
    rule_id: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    severidad: Mapped[str] = mapped_column(String(8), nullable=False)
    pagina: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ubicacion: Mapped[dict] = mapped_column(JSONVariant, nullable=False, default=dict)
    evidencia: Mapped[dict] = mapped_column(JSONVariant, nullable=False, default=dict)
    valor_encontrado: Mapped[str | None] = mapped_column(Text, nullable=True)
    valor_esperado: Mapped[str | None] = mapped_column(Text, nullable=True)
    requires_llm: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "manuscript_id": self.manuscript_id,
            "run_id": self.run_id,
            "rule_id": self.rule_id,
            "severidad": self.severidad,
            "pagina": self.pagina,
            "ubicacion": self.ubicacion,
            "evidencia": self.evidencia,
            "valor_encontrado": self.valor_encontrado,
            "valor_esperado": self.valor_esperado,
            "requires_llm": self.requires_llm,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
