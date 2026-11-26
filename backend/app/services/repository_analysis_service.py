import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from pydriller import Commit, Repository
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repository_checkout import (
    build_authenticated_url,
    with_cloned_repository,
)
from app.models.analyse_model import AnalysisStatus
from app.repositories.analysis_repository import AnalysisRepository
from app.schemas.metrics_schemas import AnalysisResult, RepositoryMetrics
from app.services.metrics.api_metrics import (
    calculate_mutual_pr_review,
    calculate_stale_branches,
    calculate_team_engagement,
    fetch_github_activity_logins,
    calculate_pr_first_response_time,
)
from app.services.metrics.git_metrics import (
    calculate_changes_volume_distribution,
    calculate_commit_messages_quality,
    calculate_deadline_activity,
    calculate_repository_cleanliness,
    calculate_work_regularity,
)
from app.services.metrics.repo_files_metrics import calculate_readme_completeness

logger = logging.getLogger(__name__)


class RepositoryAnalysisService:
    def __init__(self, session: AsyncSession) -> None:
        self._analyses = AnalysisRepository(session)

    async def run(
        self,
        analysis_id: str,
        github_token: str | None = None,
        sprint_start: datetime | None = None,
        sprint_end: datetime | None = None,
        team_members: list[dict] | None = None,
    ) -> None:
        analysis = await self._analyses.get(analysis_id)
        if analysis is None:
            return

        analysis.status = AnalysisStatus.IN_PROGRESS
        await self._analyses.save()
        await self._analyses.commit()

        try:
            metrics = await self._collect_metrics(
                analysis.repo_url,
                github_token,
                sprint_start,
                sprint_end,
                team_members,
            )
            analysis.metrics_result = metrics.model_dump(mode="json")
            analysis.status = AnalysisStatus.COMPLETED
        except Exception as exc:
            logger.exception("Repository analysis %s failed", analysis_id)
            error_text = str(exc).strip() or f"{type(exc).__name__}: {exc!r}"
            if github_token:
                error_text = error_text.replace(github_token, "***")
            analysis.status = AnalysisStatus.FAILED
            analysis.error_message = error_text
        finally:
            analysis.completed_at = datetime.now(timezone.utc)
            await self._analyses.save()
            await self._analyses.commit()

    async def _collect_metrics(
        self,
        repo_url: str,
        github_token: str | None,
        sprint_start: datetime | None,
        sprint_end: datetime | None,
        team_members: list[dict] | None,
    ) -> RepositoryMetrics:
        clone_url = build_authenticated_url(repo_url, github_token)
        local_task = asyncio.to_thread(
            with_cloned_repository,
            clone_url,
            lambda path: _analyze_local_repository(path, sprint_start, sprint_end),
        )
        activity_task = fetch_github_activity_logins(
            repo_url, github_token, sprint_start, sprint_end
        )
        stale_task = calculate_stale_branches(repo_url, github_token, 14)
        response_task = calculate_pr_first_response_time(
            repo_url, github_token, sprint_start, sprint_end
        )
        review_task = calculate_mutual_pr_review(
            repo_url, github_token, sprint_start, sprint_end, team_members
        )

        (git_metrics, commits), activity, stale, response, reviews = await asyncio.gather(
            local_task, activity_task, stale_task, response_task, review_task
        )
        engagement = calculate_team_engagement(commits, activity, team_members)

        return RepositoryMetrics.model_validate(
            {
                "team_engagement": engagement,
                "stale_branches": stale,
                "pr_first_response_time": response,
                "mutual_pr_review": reviews,
                **git_metrics,
            }
        )


def _analyze_local_repository(
    repo_path: Path,
    sprint_start: datetime | None,
    sprint_end: datetime | None,
) -> tuple[dict, list[Commit]]:
    commits = list(
        Repository(
            path_to_repo=str(repo_path),
            since=sprint_start,
            to=sprint_end,
        ).traverse_commits()
    )
    return (
        {
            "sprint_commits_counts": len(commits),
            "changes_volume_distribution": calculate_changes_volume_distribution(commits),
            "commits_quality": calculate_commit_messages_quality(commits),
            "repository_cleanliness": calculate_repository_cleanliness(commits),
            "readme_analyse": calculate_readme_completeness(repo_path),
            "regularity_heatmap": calculate_work_regularity(commits),
            "deadline_activity": calculate_deadline_activity(commits, sprint_end),
        },
        commits,
    )
