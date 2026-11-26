
from __future__ import annotations
from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import DateTime, func, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.db.base import Base


if TYPE_CHECKING:
    from app.models.project_model import Project
    from app.models.user_model import User
    from app.models.team_member_model import TeamMember

class Team(Base):
    __tablename__ = "teams"
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    owner: Mapped["User"] = relationship(back_populates="owned_teams")
    members: Mapped[List["TeamMember"]] = relationship(back_populates="team")
    projects: Mapped[List["Project"]] = relationship(back_populates="team")
