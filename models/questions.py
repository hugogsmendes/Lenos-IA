from typing import TYPE_CHECKING
from database.postgres import Base
from uuid import uuid4
from datetime import datetime
from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .answers import Answer

class Question (Base):

    __tablename__ = "questions"

    id: Mapped[UUID] = mapped_column(UUID, primary_key = True, default = uuid4)
    description: Mapped[str] = mapped_column(String, nullable = False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone = True), server_default = func.now(), nullable = False)

    answers: Mapped[list["Answer"]] = relationship(back_populates = "question", lazy = "subquery")

    
    