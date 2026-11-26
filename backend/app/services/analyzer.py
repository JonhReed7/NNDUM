

from datetime import datetime

from app.db.base import AsyncSessionLocal
from app.services.repository_analysis_service import RepositoryAnalysisService


async def run_repository_analysis(
    analysis_id: str,
    github_token: str | None = None,
    sprint_start: datetime | None = None,
    sprint_end: datetime | None = None,
    team_members: list[dict] | None = None,
) -> None:
    async with AsyncSessionLocal() as session:
        await RepositoryAnalysisService(session).run(
            analysis_id=analysis_id,
            github_token=github_token,
            sprint_start=sprint_start,
            sprint_end=sprint_end,
            team_members=team_members,
        )
