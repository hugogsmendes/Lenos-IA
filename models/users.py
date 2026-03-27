from typing import TYPE_CHECKING
from utils.database import Base
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .analyses import Analyse
    from .answers import Answer


class User (Base):

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid = True), primary_key = True, default = uuid4)
    name: Mapped[str] = mapped_column(String, nullable = False)
    email: Mapped[str] = mapped_column(String, nullable = False, unique = True)
    phone: Mapped[str] = mapped_column(String, nullable = False, unique = True)
    password_hash: Mapped[str] = mapped_column(String, nullable = False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        server_default = func.now(),
        nullable = False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        server_default = func.now(),
        onupdate = func.now(),
        nullable = False)
    
    analyses: Mapped[list["Analyse"]] = relationship(back_populates = "user", lazy = "subquery")
    answers: Mapped[list["Answer"]] = relationship(back_populates = "user", lazy = "subquery")