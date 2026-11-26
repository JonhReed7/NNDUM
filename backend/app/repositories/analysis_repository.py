from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analyse_model import Analyse


class AnalysisRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, analysis_id: str) -> Analyse | None:
        return await self._session.scalar(
            select(Analyse).where(Analyse.id == analysis_id)
        )

    async def add(self, analysis: Analyse) -> None:
        self._session.add(analysis)
        await self._session.flush()

    async def save(self) -> None:
        await self._session.flush()

    async def commit(self) -> None:
        await self._session.commit()
