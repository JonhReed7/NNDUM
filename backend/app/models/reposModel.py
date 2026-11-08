# models.py
from sqlalchemy import String, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class Repository(Base):
    __tablename__ = "repositories"

    repo_url: Mapped[str] = mapped_column(String, unique=True, index=True)
    commits_count: Mapped[int] = mapped_column(Integer, default=0)
    code_churn: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[float] = mapped_column(Float, default=0.0)