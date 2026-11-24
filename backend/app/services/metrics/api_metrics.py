import asyncio
from datetime import datetime, timezone
from statistics import median
from urllib.parse import urlparse
import httpx
from pydriller import Commit


def _parse_repo_owner_and_name(repo_url: str) -> tuple[str, str]:
    """Извлекает owner и repo из URL вида https://github.com/owner/repo.git"""
    path = urlparse(str(repo_url)).path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    parts = path.split("/")
    if len(parts) < 2:
        raise ValueError(f"Некорректный URL репозитория: {repo_url}")
    return parts[-2], parts[-1]


def _is_within_sprint(
    dt_str: str | None,
    sprint_start: datetime | None,
    sprint_end: datetime | None,
) -> bool:
    """Проверяет, попадает ли ISO-дата из API в границы спринта."""
    if not dt_str:
        return False
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    if sprint_start and dt < sprint_start:
        return False
    if sprint_end and dt > sprint_end:
        return False
    return True


async def fetch_github_activity_logins(
    repo_url: str,
    github_token: str | None = None,
    sprint_start: datetime | None = None,
    sprint_end: datetime | None = None,
) -> dict:
    """
    Собирает через GitHub API:
    - список всех коллабораторов (если команда не задана вручную)
    - логины тех, кто создавал PR за спринт
    - логины тех, кто оставлял комментарии в PR/Issues или делал ревью за спринт
    """
    owner, repo = _parse_repo_owner_and_name(repo_url)
    base_url = f"https://api.github.com/repos/{owner}/{repo}"

    headers = {"Accept": "application/vnd.github+json"}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    pr_authors: set[str] = set()
    commenters: set[str] = set()
    collaborators: list[str] = []

    async with httpx.AsyncClient(headers=headers, timeout=15.0) as client:
        # 1. Получаем коллабораторов репозитория (резервный список команды)
        collab_resp = await client.get(f"{base_url}/collaborators")
        if collab_resp.status_code == 200:
            collaborators = [
                user["login"].lower()
                for user in collab_resp.json()
                if user.get("type") == "User"
            ]

        # 2. Получаем Pull Requests за период
        prs_resp = await client.get(
            f"{base_url}/pulls",
            params={"state": "all", "sort": "updated", "direction": "desc", "per_page": 100},
        )
        if prs_resp.status_code == 200:
            for pr in prs_resp.json():
                if _is_within_sprint(pr.get("created_at"), sprint_start, sprint_end):
                    login = pr.get("user", {}).get("login")
                    if login:
                        pr_authors.add(login.lower())

                # Проверяем ревью по каждому свежему PR (это пригодится и для Метрик №7, №9, №14)
                if _is_within_sprint(pr.get("updated_at"), sprint_start, sprint_end):
                    pr_number = pr["number"]
                    reviews_resp = await client.get(f"{base_url}/pulls/{pr_number}/reviews")
                    if reviews_resp.status_code == 200:
                        for rev in reviews_resp.json():
                            if _is_within_sprint(rev.get("submitted_at"), sprint_start, sprint_end):
                                rev_login = rev.get("user", {}).get("login")
                                if rev_login:
                                    commenters.add(rev_login.lower())

        # 3. Получаем комментарии в Issues и Pull Requests (общая лента комментариев репо)
        comments_params = {"per_page": 100}
        if sprint_start:
            comments_params["since"] = sprint_start.isoformat()

        comments_resp = await client.get(f"{base_url}/issues/comments", params=comments_params)
        if comments_resp.status_code == 200:
            for comment in comments_resp.json():
                if _is_within_sprint(comment.get("created_at"), sprint_start, sprint_end):
                    c_login = comment.get("user", {}).get("login")
                    if c_login:
                        commenters.add(c_login.lower())

    return {
        "collaborators": collaborators,
        "pr_authors": pr_authors,
        "commenters": commenters,
    }


def calculate_team_engagement(
    commits: list[Commit],
    github_activity: dict,
    team_members: list[dict] | None = None,
) -> dict:
    """
    Метрика №1: Вовлечённость участников.
    Считает долю участников команды, у которых за спринт был хотя бы 1 коммит, PR или комментарий/ревью.
    """
    # Собираем все email и имена авторов из коммитов спринта
    active_commit_emails: set[str] = set()
    for commit in commits:
        if commit.merge:
            continue
        if commit.author.email:
            active_commit_emails.add(commit.author.email.lower())

    pr_authors: set[str] = github_activity.get("pr_authors", set())
    commenters: set[str] = github_activity.get("commenters", set())

    # Если состав команды не передан явно — формируем его из коллабораторов репозитория
    if not team_members:
        logins = set(github_activity.get("collaborators", [])) | pr_authors | commenters
        team_members = [
            {"name": login, "github_login": login, "emails": []}
            for login in sorted(logins)
        ]

    members_report = []
    active_members_count = 0

    for member in team_members:
        login = (member.get("github_login") or "").lower()
        emails = {e.lower() for e in member.get("emails", [])}

        has_commit = bool(emails & active_commit_emails) or (
            # Фоллбэк: если в GitHub noreply-почте зашит логин (например, 12345+annadev@users.noreply.github.com)
            bool(login) and any(login in email for email in active_commit_emails)
        )
        has_pr = login in pr_authors
        has_comment = login in commenters

        is_active = has_commit or has_pr or has_comment
        if is_active:
            active_members_count += 1

        members_report.append({
            "name": member.get("name") or login,
            "github_login": login or None,
            "is_active": is_active,
            "has_commit": has_commit,
            "has_pr": has_pr,
            "has_comment_or_review": has_comment,
        })

    total_members = len(team_members)
    engagement_percent = (
        round((active_members_count / total_members) * 100, 2)
        if total_members > 0
        else 0.0
    )

    return {
        "total_team_members": total_members,
        "active_members_count": active_members_count,
        "engagement_percent": engagement_percent,
        "members": members_report,
    }



async def calculate_stale_branches(
    repo_url: str,
    github_token: str | None = None,
    stale_days_threshold: int = 7,
    ignore_branches: set[str] | None = None,
) -> dict:
    """
    Метрика №10: Ветки без активности.
    Возвращает количество и список открытых веток, в которых не было новых коммитов
    дольше `stale_days_threshold` дней (по умолчанию 7).
    """
    if ignore_branches is None:
        ignore_branches = {"main", "master", "develop", "dev"}

    owner, repo = _parse_repo_owner_and_name(repo_url)
    base_url = f"https://api.github.com/repos/{owner}/{repo}"

    headers = {"Accept": "application/vnd.github+json"}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    now = datetime.now(timezone.utc)

    async with httpx.AsyncClient(headers=headers, timeout=15.0) as client:
        # 1. Получаем все открытые ветки
        branches_resp = await client.get(
            f"{base_url}/branches",
            params={"per_page": 100},
        )
        if branches_resp.status_code != 200:
            raise RuntimeError(
                f"Не удалось получить ветки репозитория (HTTP {branches_resp.status_code})"
            )

        raw_branches = branches_resp.json()

        # Фильтруем базовые ветки (main, master и т.д.)
        target_branches = [
            b for b in raw_branches
            if b.get("name") not in ignore_branches
        ]

        # 2. Вспомогательная корутина для получения даты последнего коммита конкретной ветки
        async def _get_branch_activity(branch_obj: dict) -> dict | None:
            branch_name = branch_obj["name"]
            commit_sha = branch_obj["commit"]["sha"]

            commit_resp = await client.get(f"{base_url}/commits/{commit_sha}")
            if commit_resp.status_code != 200:
                return None

            commit_data = commit_resp.json()
            commit_info = commit_data.get("commit", {})
            # Берем дату коммитера (когда коммит реально попал в ветку)
            date_str = (
                commit_info.get("committer", {}).get("date")
                or commit_info.get("author", {}).get("date")
            )
            if not date_str:
                return None

            last_commit_dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            days_inactive = round((now - last_commit_dt).total_seconds() / 86400, 1)

            author_login = (
                (commit_data.get("author") or {}).get("login")
                or commit_info.get("author", {}).get("name")
            )

            return {
                "branch_name": branch_name,
                "last_commit_sha": commit_sha[:7],
                "last_commit_date": last_commit_dt.isoformat(),
                "last_author": author_login,
                "days_inactive": days_inactive,
                "is_stale": days_inactive >= stale_days_threshold,
            }

        # 3. Запрашиваем детали по всем веткам параллельно
        results = await asyncio.gather(
            *(_get_branch_activity(b) for b in target_branches)
        )

    evaluated_branches = [r for r in results if r is not None]
    stale_branches = sorted(
        [b for b in evaluated_branches if b["is_stale"]],
        key=lambda x: x["days_inactive"],
        reverse=True,
    )

    total_feature_branches = len(evaluated_branches)
    stale_count = len(stale_branches)
    stale_share_percent = (
        round((stale_count / total_feature_branches) * 100, 2)
        if total_feature_branches > 0
        else 0.0
    )

    return {
        "stale_days_threshold": stale_days_threshold,
        "total_open_feature_branches": total_feature_branches,
        "stale_branches_count": stale_count,
        "stale_branches_share_percent": stale_share_percent,
        "stale_branches": stale_branches,
    }


def _parse_iso_dt(dt_str: str | None) -> datetime | None:
    if not dt_str:
        return None
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))


def _is_valid_colleague(user_obj: dict | None, pr_author_login: str) -> bool:
    """Проверяет, что событие оставил коллега, а не сам автор PR и не бот."""
    if not user_obj:
        return False
    login = (user_obj.get("login") or "").lower()
    user_type = user_obj.get("type") or ""
    if not login or login == pr_author_login:
        return False
    if user_type == "Bot" or login.endswith("[bot]"):
        return False
    return True


async def calculate_pr_first_response_time(
    repo_url: str,
    github_token: str | None = None,
    sprint_start: datetime | None = None,
    sprint_end: datetime | None = None,
) -> dict:
    """
    Метрика №7: Время до первого отклика на PR.
    Считает время (в часах и минутах) от создания PR до первого ревью или комментария от коллеги.
    """
    owner, repo = _parse_repo_owner_and_name(repo_url)
    base_url = f"https://api.github.com/repos/{owner}/{repo}"

    headers = {"Accept": "application/vnd.github+json"}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    async with httpx.AsyncClient(headers=headers, timeout=15.0) as client:
        # 1. Получаем список всех PR (открытых и закрытых/смерженных)
        prs_resp = await client.get(
            f"{base_url}/pulls",
            params={"state": "all", "sort": "created", "direction": "desc", "per_page": 100},
        )
        if prs_resp.status_code != 200:
            raise RuntimeError(
                f"Не удалось получить список PR (HTTP {prs_resp.status_code})"
            )

        # Отбираем PR, созданные в рамках спринта (и исключаем черновики-драфты, если нужно)
        sprint_prs = [
            pr for pr in prs_resp.json()
            if _is_within_sprint(pr.get("created_at"), sprint_start, sprint_end)
        ]

        # 2. Вспомогательная корутина для анализа откликов по одному PR
        async def _analyze_single_pr(pr: dict) -> dict:
            pr_number = pr["number"]
            pr_title = pr.get("title", "")
            pr_author = (pr.get("user", {}).get("login") or "").lower()
            created_at = _parse_iso_dt(pr.get("created_at"))

            # Параллельно запрашиваем все 3 типа активности в PR:
            # 1) ревью, 2) общие комментарии в PR, 3) комментарии к строкам кода
            reviews_req = client.get(f"{base_url}/pulls/{pr_number}/reviews")
            issue_comments_req = client.get(f"{base_url}/issues/{pr_number}/comments")
            review_comments_req = client.get(f"{base_url}/pulls/{pr_number}/comments")

            reviews_resp, issue_comments_resp, review_comments_resp = await asyncio.gather(
                reviews_req, issue_comments_req, review_comments_req
            )

            colleague_responses: list[tuple[datetime, str, str]] = []

            # А) Проверяем reviews (submitted_at)
            if reviews_resp.status_code == 200:
                for rev in reviews_resp.json():
                    if rev.get("state") == "PENDING":
                        continue
                    user = rev.get("user")
                    dt = _parse_iso_dt(rev.get("submitted_at"))
                    if dt and created_at and dt >= created_at and _is_valid_colleague(user, pr_author):
                        colleague_responses.append((dt, user["login"], f"review:{rev.get('state')}"))

            # Б) Проверяем общие комментарии в PR (created_at)
            if issue_comments_resp.status_code == 200:
                for comment in issue_comments_resp.json():
                    user = comment.get("user")
                    dt = _parse_iso_dt(comment.get("created_at"))
                    if dt and created_at and dt >= created_at and _is_valid_colleague(user, pr_author):
                        colleague_responses.append((dt, user["login"], "comment"))

            # В) Проверяем комментарии к строкам кода (created_at)
            if review_comments_resp.status_code == 200:
                for r_comment in review_comments_resp.json():
                    user = r_comment.get("user")
                    dt = _parse_iso_dt(r_comment.get("created_at"))
                    if dt and created_at and dt >= created_at and _is_valid_colleague(user, pr_author):
                        colleague_responses.append((dt, user["login"], "inline_comment"))

            if not colleague_responses or not created_at:
                return {
                    "pr_number": pr_number,
                    "title": pr_title,
                    "author": pr_author,
                    "state": pr.get("state"),
                    "has_response": False,
                    "responder": None,
                    "response_type": None,
                    "response_time_hours": None,
                    "response_time_minutes": None,
                }

            # Находим самый первый отклик от коллеги
            first_dt, responder_login, resp_type = min(colleague_responses, key=lambda x: x[0])
            delta_seconds = max((first_dt - created_at).total_seconds(), 0.0)

            return {
                "pr_number": pr_number,
                "title": pr_title,
                "author": pr_author,
                "state": pr.get("state"),
                "has_response": True,
                "responder": responder_login,
                "response_type": resp_type,
                "response_time_hours": round(delta_seconds / 3600, 2),
                "response_time_minutes": round(delta_seconds / 60, 1),
            }

        # 3. Обрабатываем все PR спринта конкурентно
        pr_results = await asyncio.gather(*(_analyze_single_pr(pr) for pr in sprint_prs))

    answered_prs = [p for p in pr_results if p["has_response"]]
    unanswered_prs = [p for p in pr_results if not p["has_response"]]

    response_hours_list = [p["response_time_hours"] for p in answered_prs]
    avg_hours = round(sum(response_hours_list) / len(response_hours_list), 2) if response_hours_list else None
    med_hours = round(median(response_hours_list), 2) if response_hours_list else None

    return {
        "total_prs_in_sprint": len(pr_results),
        "answered_prs_count": len(answered_prs),
        "unanswered_prs_count": len(unanswered_prs),
        "average_response_time_hours": avg_hours,
        "median_response_time_hours": med_hours,
        "prs": pr_results,
    }


async def calculate_mutual_pr_review(
    repo_url: str,
    github_token: str | None = None,
    sprint_start: datetime | None = None,
    sprint_end: datetime | None = None,
    team_members: list[dict] | None = None,
) -> dict:
    """
    Метрика №9: Взаимное ревью PR.
    Считает долю участников команды, которые за спринт оставили хотя бы один
    комментарий или провели ревью чужого PR до его слияния/закрытия.
    """
    owner, repo = _parse_repo_owner_and_name(repo_url)
    base_url = f"https://api.github.com/repos/{owner}/{repo}"

    headers = {"Accept": "application/vnd.github+json"}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    async with httpx.AsyncClient(headers=headers, timeout=15.0) as client:
        # 1. Получаем коллабораторов (на случай если team_members не передан)
        collaborators: set[str] = set()
        if not team_members:
            collab_resp = await client.get(f"{base_url}/collaborators")
            if collab_resp.status_code == 200:
                collaborators = {
                    u["login"].lower()
                    for u in collab_resp.json()
                    if u.get("type") == "User"
                }

        # 2. Получаем все PR репозитория и фильтруем по границам спринта
        prs_resp = await client.get(
            f"{base_url}/pulls",
            params={"state": "all", "sort": "updated", "direction": "desc", "per_page": 100},
        )
        if prs_resp.status_code != 200:
            raise RuntimeError(
                f"Не удалось получить список PR (HTTP {prs_resp.status_code})"
            )

        sprint_prs = [
            pr for pr in prs_resp.json()
            if _is_within_sprint(pr.get("created_at"), sprint_start, sprint_end)
            or _is_within_sprint(pr.get("merged_at"), sprint_start, sprint_end)
        ]

        # 3. Проверяем каждый PR на наличие ревью/комментариев от коллег ДО слияния
        async def _collect_pr_reviewers(pr: dict) -> dict:
            pr_number = pr["number"]
            pr_author = (pr.get("user", {}).get("login") or "").lower()
            created_at = _parse_iso_dt(pr.get("created_at"))
            # Граница ревью: момент мержа (или закрытия), если PR уже закрыт
            cutoff_dt = _parse_iso_dt(pr.get("merged_at")) or _parse_iso_dt(pr.get("closed_at"))

            reviews_resp, issue_comments_resp, review_comments_resp = await asyncio.gather(
                client.get(f"{base_url}/pulls/{pr_number}/reviews"),
                client.get(f"{base_url}/issues/{pr_number}/comments"),
                client.get(f"{base_url}/pulls/{pr_number}/comments"),
            )

            reviewers_for_pr: set[str] = set()

            def _is_before_merge(dt: datetime | None) -> bool:
                if not dt:
                    return False
                if created_at and dt < created_at:
                    return False
                if cutoff_dt and dt > cutoff_dt:
                    return False
                if sprint_start and dt < sprint_start:
                    return False
                if sprint_end and dt > sprint_end:
                    return False
                return True

            if reviews_resp.status_code == 200:
                for rev in reviews_resp.json():
                    if rev.get("state") == "PENDING":
                        continue
                    user = rev.get("user")
                    dt = _parse_iso_dt(rev.get("submitted_at"))
                    if _is_before_merge(dt) and _is_valid_colleague(user, pr_author):
                        reviewers_for_pr.add(user["login"].lower())

            if issue_comments_resp.status_code == 200:
                for comment in issue_comments_resp.json():
                    user = comment.get("user")
                    dt = _parse_iso_dt(comment.get("created_at"))
                    if _is_before_merge(dt) and _is_valid_colleague(user, pr_author):
                        reviewers_for_pr.add(user["login"].lower())

            if review_comments_resp.status_code == 200:
                for r_comment in review_comments_resp.json():
                    user = r_comment.get("user")
                    dt = _parse_iso_dt(r_comment.get("created_at"))
                    if _is_before_merge(dt) and _is_valid_colleague(user, pr_author):
                        reviewers_for_pr.add(user["login"].lower())

            return {
                "pr_number": pr_number,
                "author": pr_author,
                "reviewers": sorted(reviewers_for_pr),
                "has_peer_review": len(reviewers_for_pr) > 0,
            }

        pr_reviews_data = await asyncio.gather(*(_collect_pr_reviewers(pr) for pr in sprint_prs))

    # Собираем множество всех уникальных участников, ревьюивших чужие PR
    all_peer_reviewers: set[str] = set()
    reviewed_prs_count = 0
    for item in pr_reviews_data:
        all_peer_reviewers.update(item["reviewers"])
        if item["has_peer_review"]:
            reviewed_prs_count += 1

    # Формируем список команды для расчёта доли
    if team_members:
        roster = [
            {
                "name": m.get("name") or m.get("github_login"),
                "github_login": (m.get("github_login") or "").lower(),
            }
            for m in team_members
            if m.get("github_login")
        ]
    else:
        all_logins = collaborators | all_peer_reviewers | {p["author"] for p in pr_reviews_data if p["author"]}
        roster = [{"name": login, "github_login": login} for login in sorted(all_logins)]

    members_breakdown = []
    reviewers_in_team_count = 0
    for member in roster:
        login = member["github_login"]
        did_review = login in all_peer_reviewers
        if did_review:
            reviewers_in_team_count += 1
        members_breakdown.append({
            "name": member["name"],
            "github_login": login,
            "reviewed_others_prs": did_review,
            "reviewed_prs_count": sum(1 for p in pr_reviews_data if login in p["reviewers"]),
        })

    total_members = len(roster)
    mutual_review_share = (
        round((reviewers_in_team_count / total_members) * 100, 2)
        if total_members > 0
        else 0.0
    )
    total_prs = len(pr_reviews_data)
    reviewed_prs_share = (
        round((reviewed_prs_count / total_prs) * 100, 2)
        if total_prs > 0
        else 0.0
    )

    return {
        "total_team_members": total_members,
        "reviewers_count": reviewers_in_team_count,
        "mutual_review_share_percent": mutual_review_share,
        "total_prs_checked": total_prs,
        "reviewed_prs_count": reviewed_prs_count,
        "reviewed_prs_share_percent": reviewed_prs_share,
        "members": members_breakdown,
    }