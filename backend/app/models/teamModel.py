
from __future__ import annotations
from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import DateTime, func, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from db.base import Base


if TYPE_CHECKING:
    from models.projectModel import Project
    from models.userModel import User
    from models.teamMemberModel import TeamMember

class Team(Base):
    __tablename__ = "teams"
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    owner: Mapped["User"] = relationship(back_populates="owned_teams")
    members: Mapped[List["TeamMember"]] = relationship(back_populates="team")
    projects: Mapped[List["Project"]] = relationship(back_populates="team")
