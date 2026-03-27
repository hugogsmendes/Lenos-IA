from typing import TYPE_CHECKING
from database.postgres import Base
from uuid import uuid4
from datetime import datetime
from sqlalchemy import DateTime, String, func, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .users import User
    from .comments import Comment
    from .reports import Report

class Analyse (Base):

    __tablename__ = "analyses"

    id: Mapped[UUID] = mapped_column(UUID, primary_key = True, default = uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("users.id"), nullable = False)
    video_url: Mapped[str] = mapped_column(String, nullable = False)
    youtube_video_id: Mapped[str] = mapped_column(String, nullable = False)
    status: Mapped[str] = mapped_column(
        Enum("pending", "done", "failed", name = "analysis_status"),
        nullable = False,
        server_default = "pending",
    )
    request_at: Mapped[datetime] = mapped_column(DateTime(timezone = True), server_default = func.now(), nullable = False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone = True), nullable = True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone = True), server_default = func.now(), nullable = False)

    user: Mapped["User"] = relationship(back_populates = "analyses", lazy = "subquery")
    comments: Mapped[list["Comment"]] = relationship(back_populates = "analysis", lazy = "subquery")
    report: Mapped["Report"] = relationship(back_populates = "analysis", lazy = "subquery", uselist = False)


