from typing import TYPE_CHECKING
from database.postgres_client import Base
from uuid import uuid4
from datetime import datetime
from sqlalchemy import DateTime, String, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .users import User

class Oauth (Base):

    __tablename__ = "oauths"

    id: Mapped[UUID] = mapped_column(UUID, primary_key = True, default = uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("users.id", ondelete = "CASCADE"), nullable = False)
    access_token: Mapped[str] = mapped_column(String, nullable = False)
    refresh_token: Mapped[str] = mapped_column(String, nullable = False)
    channel_id: Mapped[str] = mapped_column(String, nullable = True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        server_default = func.now(),
        nullable = False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        server_default = func.now(),
        onupdate = func.now(),
        nullable = False)

    user: Mapped["User"] = relationship(back_populates = "oauth", lazy = "subquery", passive_deletes = True)
    