from typing import TYPE_CHECKING
from sessions.database import Base
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import DateTime, String, func, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .analyses import Analyse

class Report (Base):

    __tablename__ = "reports"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid = True), primary_key = True, default = uuid4)
    analyses_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid = True), ForeignKey("analyses.id"), nullable = False, unique = True)
    prompt: Mapped[str] = mapped_column(String, nullable = False)
    report_markdown: Mapped[str] = mapped_column(String, nullable = False)
    report_title: Mapped[str] = mapped_column(String, nullable = False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable = True)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable = True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone = True), server_default = func.now(), nullable = False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        server_default = func.now(),
        onupdate = func.now(),
        nullable = False)

    analysis: Mapped["Analyse"] = relationship(back_populates = "report", lazy = "subquery")