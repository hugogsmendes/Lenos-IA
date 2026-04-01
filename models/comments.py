from typing import TYPE_CHECKING
from database.postgres import Base
from uuid import uuid4
from datetime import datetime
from sqlalchemy import DateTime, String, func, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .analyses import Analyse

class Comment (Base):

    __tablename__ = "comments"

    id: Mapped[UUID] = mapped_column(UUID, primary_key = True, default = uuid4)
    analyses_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("analyses.id", ondelete = "CASCADE"), nullable = False)
    author_name: Mapped[str] = mapped_column(String, nullable = False)
    like_count: Mapped[int] = mapped_column(Integer, nullable = False)
    text_processing: Mapped[str] = mapped_column(String, nullable = False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone = True), server_default = func.now(), nullable = False)

    analysis: Mapped["Analyse"] = relationship(back_populates = "comments", lazy = "subquery", passive_deletes = True)
