
from __future__ import annotations
from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from models.sprintModel import Sprint
    from models.teamModel import Team

class Project(Base):
    __tablename__ = 'projects'
    team_id: Mapped[str] = mapped_column(ForeignKey('teams.id'), nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    repo_url: Mapped[str] = mapped_column(nullable=False)
    branch: Mapped[str] = mapped_column(default="main")
    timezone: Mapped[str] = mapped_column(default="UTC+0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    team: Mapped["Team"] = relationship(back_populates="projects")
    sprints: Mapped[List["Sprint"]] = relationship(back_populates="project", cascade="all, delete-orphan")


