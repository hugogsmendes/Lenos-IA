from src.database.postgres_client import Base
from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import DateTime, String, func, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
import uuid

if TYPE_CHECKING:
    from .users import User
    from .comments import Comment
    from .reports import Report

class Analysis (Base):

    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key = True, default = uuid.uuid4())
    user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("users.id", ondelete = "CASCADE"), nullable = False)
    video_url: Mapped[str] = mapped_column(String, nullable = False)
    youtube_video_id: Mapped[str] = mapped_column(String, nullable = False)
    status: Mapped[enum.Enum] = mapped_column(
        Enum("pending", "done", "failed", name = "analysis_status"),
        nullable = False,
        server_default = "pending",
    )
    request_at: Mapped[datetime] = mapped_column(DateTime(timezone = True), server_default = func.now(), nullable = False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone = True), onupdate = func.now(), nullable = True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone = True), server_default = func.now(), nullable = False)

    user: Mapped["User"] = relationship(back_populates = "analyses", lazy = "subquery", passive_deletes = True)
    comments: Mapped[list["Comment"]] = relationship(back_populates = "analysis", lazy = "subquery", cascade = "all, delete")
    report: Mapped["Report"] = relationship(back_populates = "analysis", lazy = "subquery", uselist = False, cascade = "all, delete")


