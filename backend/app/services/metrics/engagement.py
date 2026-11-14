from datetime import datetime
from typing import Set, Optional
from pydriller import Repository

def get_all_contributors(repo_url: str) -> set:
    contributors = set()
    
    for commit in Repository(repo_url).traverse_commits():
        if commit.author and commit.author.email:
            contributors.add(commit.author.email.lower().strip())
    return contributors


def calculate_engagement(
        repo_path: str,
        all_team_members: Set[str],
        pr_comment_authors: Optional[Set[str]] = None
) -> dict:
    """
    Рассчитывает метрику №1 «Вовлеченность участников» за спринт.

    :param repo_path: Путь к локальному клону репозитория (или ссылка для PyDriller).
    :param all_team_members: Множество всех участников команды (например, по email или username).
    :param pr_comment_authors: Множество участников, оставивших PR или комментарии в GitVerse за спринт.
    :return: Словарь с деталями метрики (доля и список вовлеченных).
    """
    if pr_comment_authors is None:
        pr_comment_authors = set()

    active_authors: Set[str] = set(pr_comment_authors)

    for commit in Repository(repo_path).traverse_commits():
        author_id = commit.author.email.lower().strip()
        active_authors.add(author_id)

    normalized_team = {member.lower().strip() for member in all_team_members}

    if not normalized_team:
        return {
            "engagement_rate": 0.0,
            "engaged_count": 0,
            "total_members": 0,
            "inactive_members": []
        }

    engaged_members = active_authors.intersection(normalized_team)
    inactive_members = normalized_team - active_authors

    rate = len(engaged_members) / len(normalized_team)

    return {
        "engagement_rate": round(rate, 2),
        "engaged_count": len(engaged_members),
        "total_members": len(normalized_team),
        "inactive_members": list(inactive_members)
    }