
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


if TYPE_CHECKING:
    from models.teamModel import Team
    from models.userModel import User

class TeamMember(Base):
    __tablename__ = 'team_members'
    team_id: Mapped[str] = mapped_column(ForeignKey('teams.id'), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), nullable=False)
    role: Mapped[str]
    git_email: Mapped[str]

    team: Mapped["Team"] = relationship(back_populates='members')
    user: Mapped["User"] = relationship(back_populates='team_memberships')




