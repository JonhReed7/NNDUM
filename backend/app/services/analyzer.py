import asyncio
import os
import shutil
import tempfile
from datetime import datetime, timezone
from urllib.parse import urlparse

from git import Repo
from pydriller import Commit, Repository
from sqlalchemy import select

from app.db.base import AsyncSessionLocal
from app.models.analyseModel import Analyse, AnalysisStatus
from app.services.metrics.git_metrics import (
    calculate_changes_volume_distribution,
    calculate_commit_messages_quality,
    calculate_repository_cleanliness,
    calculate_work_regularity, calculate_deadline_activity,
)
from app.services.metrics.api_metrics import (
    calculate_team_engagement,
    fetch_github_activity_logins, calculate_stale_branches, calculate_pr_first_response_time,
    calculate_mutual_pr_review,
)
from app.services.metrics.repo_files_metrics import calculate_readme_completeness


def _force_remove_readonly(func, path, exc_info):
    """РЎР±СЂР°СЃС‹РІР°РµС‚ Р°С‚СЂРёР±СѓС‚ Read-Only Сѓ С„Р°Р№Р»РѕРІ .git РЅР° Windows РїРµСЂРµРґ СѓРґР°Р»РµРЅРёРµРј."""
    try:
        os.chmod(path, os.stat.S_IWRITE)
        func(path)
    except Exception:
        pass

def _build_auth_url(repo_url: str, token: str | None) -> str:
    """Р’СЃС‚СЂР°РёРІР°РµС‚ GitHub OAuth-С‚РѕРєРµРЅ РІ URL РґР»СЏ РґРѕСЃС‚СѓРїР° Рє РїСЂРёРІР°С‚РЅС‹Рј СЂРµРїРѕР·РёС‚РѕСЂРёСЏРј."""
    if not token:
        return repo_url
    parsed = urlparse(repo_url)
    return f"{parsed.scheme}://x-access-token:{token}@{parsed.netloc}{parsed.path}"


def _sync_analyze_repo(
    clone_url: str,
    sprint_start: datetime | None = None,
    sprint_end: datetime | None = None,
) -> tuple[dict, list[Commit]]:
    """
    РЎРёРЅС…СЂРѕРЅРЅР°СЏ С„СѓРЅРєС†РёСЏ РєР»РѕРЅРёСЂРѕРІР°РЅРёСЏ Рё РїР°СЂСЃРёРЅРіР° РєРѕРјРјРёС‚РѕРІ С‡РµСЂРµР· PyDriller.
    Р’РѕР·РІСЂР°С‰Р°РµС‚ СЃР»РѕРІР°СЂСЊ СЃ git/С„Р°Р№Р»РѕРІС‹РјРё РјРµС‚СЂРёРєР°РјРё Рё СЃРїРёСЃРѕРє РєРѕРјРјРёС‚РѕРІ СЃРїСЂРёРЅС‚Р°.
    """
    temp_dir = tempfile.mkdtemp(prefix="devpulse_")
    git_repo: Repo | None = None

    try:
        git_repo = Repo.clone_from(clone_url, temp_dir)

        repo = Repository(
            path_to_repo=temp_dir,
            since=sprint_start,
            to=sprint_end,
        )

        sprint_commits = list(repo.traverse_commits())
        volume_distribution = calculate_changes_volume_distribution(sprint_commits)
        commits_quality = calculate_commit_messages_quality(sprint_commits)
        repository_cleanliness = calculate_repository_cleanliness(sprint_commits)
        readme_analyse = calculate_readme_completeness(temp_dir)
        regularity_heatmap = calculate_work_regularity(sprint_commits)
        deadline_activity = calculate_deadline_activity(
            commits=sprint_commits,
            deadline=sprint_end,
            timezone_name="Asia/Yekaterinburg",
        )

        git_metrics = {
            "sprint_commits_counts": len(sprint_commits),
            "changes_volume_distribution": volume_distribution,
            "commits_quality": commits_quality,
            "repository_cleanliness": repository_cleanliness,
            "readme_analyse": readme_analyse,
            "regularity_heatmap": regularity_heatmap,
            "deadline_activity": deadline_activity,
        }

        return git_metrics, sprint_commits

    finally:
        # 1. РЇРІРЅРѕ Р·Р°РєСЂС‹РІР°РµРј РґРµСЃРєСЂРёРїС‚РѕСЂС‹ GitPython РїРµСЂРµРґ СѓРґР°Р»РµРЅРёРµРј РїР°РїРєРё
        if git_repo is not None:
            git_repo.close()

        # 2. Р‘РµР·РѕРїР°СЃРЅРѕ СѓРґР°Р»СЏРµРј РІСЂРµРјРµРЅРЅСѓСЋ РїР°РїРєСѓ, РёРіРЅРѕСЂРёСЂСѓСЏ Р±Р»РѕРєРёСЂРѕРІРєРё Windows
        shutil.rmtree(temp_dir, onerror=_force_remove_readonly)


async def run_repository_analysis(
    analysis_id: str,
    github_token: str | None = None,
    sprint_start: datetime | None = None,
    sprint_end: datetime | None = None,
    team_members: list[dict] | None = None,
) -> None:
    """Р¤РѕРЅРѕРІР°СЏ Р·Р°РґР°С‡Р°: СѓРїСЂР°РІР»СЏРµС‚ СЃС‚Р°С‚СѓСЃР°РјРё РІ Р‘Р” Рё Р·Р°РїСѓСЃРєР°РµС‚ РїРѕР»РЅС‹Р№ Р°РЅР°Р»РёР·."""
    async with AsyncSessionLocal() as db:
        analysis = await db.scalar(select(Analyse).where(Analyse.id == analysis_id))
        if not analysis:
            return

        # 1. РџРµСЂРµРІРѕРґРёРј СЃС‚Р°С‚СѓСЃ РІ IN_PROGRESS
        analysis.status = AnalysisStatus.IN_PROGRESS
        await db.commit()

        try:
            clone_url = _build_auth_url(analysis.repo_url, github_token)

            # 2. Р—Р°РїСѓСЃРєР°РµРј Р»РѕРєР°Р»СЊРЅС‹Р№ Git-Р°РЅР°Р»РёР· Рё Р·Р°РїСЂРѕСЃС‹ Рє GitHub API РїР°СЂР°Р»Р»РµР»СЊРЅРѕ
            git_task = asyncio.to_thread(
                _sync_analyze_repo,
                clone_url,
                sprint_start,
                sprint_end,
            )

            api_task = fetch_github_activity_logins(
                repo_url=analysis.repo_url,
                github_token=github_token,
                sprint_start=sprint_start,
                sprint_end=sprint_end,
            )

            stale_branches_task = calculate_stale_branches(
                repo_url=analysis.repo_url,
                github_token=github_token,
                stale_days_threshold=14,
            )

            pr_response_task = calculate_pr_first_response_time(
                repo_url=analysis.repo_url,
                github_token=github_token,
                sprint_start=sprint_start,
                sprint_end=sprint_end,
            )

            mutual_review_task = calculate_mutual_pr_review(
                repo_url=analysis.repo_url,
                github_token=github_token,
                sprint_start=sprint_start,
                sprint_end=sprint_end,
                team_members=team_members,
            )

            (git_metrics, sprint_commits), github_activity, stale_branches, pr_first_response, mutual_pr_review = await asyncio.gather(
                git_task,
                api_task,
                stale_branches_task,
                pr_response_task,
                mutual_review_task,
            )

            # 3. РЎС‡РёС‚Р°РµРј РњРµС‚СЂРёРєСѓ в„–1 (В«Р’РѕРІР»РµС‡С‘РЅРЅРѕСЃС‚СЊ СѓС‡Р°СЃС‚РЅРёРєРѕРІВ») РЅР° СЃС‚С‹РєРµ РєРѕРјРјРёС‚РѕРІ Рё API
            team_engagement = calculate_team_engagement(
                commits=sprint_commits,
                github_activity=github_activity,
                team_members=team_members,
            )

            # 4. РЎРѕС…СЂР°РЅСЏРµРј РёС‚РѕРіРѕРІС‹Р№ СЂРµР·СѓР»СЊС‚Р°С‚
            analysis.metrics_result = {
                "team_engagement": team_engagement,
                "stale_branches": stale_branches,
                "pr_first_response_time": pr_first_response,
                **git_metrics,
            }
            analysis.status = AnalysisStatus.COMPLETED
            analysis.completed_at = datetime.now(timezone.utc)

        except Exception as exc:
            # РЎРєСЂС‹РІР°РµРј С‚РѕРєРµРЅ РёР· С‚РµРєСЃС‚Р° РѕС€РёР±РєРё, С‡С‚РѕР±С‹ РЅРµ Р·Р°РїРёСЃР°С‚СЊ РµРіРѕ РІ Р‘Р”
            error_text = str(exc)
            if github_token:
                error_text = error_text.replace(github_token, "***")

            analysis.status = AnalysisStatus.FAILED
            analysis.error_message = error_text
            analysis.completed_at = datetime.now(timezone.utc)

        finally:
            await db.commit()