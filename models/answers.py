from typing import TYPE_CHECKING
from database.postgres import Base
from uuid import uuid4
from datetime import datetime
from sqlalchemy import DateTime, String, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .users import User
    from .questions import Question

class Answer (Base):

    __tablename__ = "answers"

    id: Mapped[UUID] = mapped_column(UUID, primary_key = True, default = uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("users.id"), nullable = False)
    questions_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("questions.id"), nullable = False)
    answer: Mapped[str] = mapped_column(String, nullable = False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone = True), server_default = func.now(), nullable = False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        server_default = func.now(),
        onupdate = func.now(),
        nullable = False)

    user: Mapped["User"] = relationship(back_populates = "answers", lazy = "subquery")
    question: Mapped["Question"] = relationship(back_populates = "answers", lazy = "subquery")