from fastapi import APIRouter
from pydriller import Repository

from services.metrics.engagement import calculate_engagement

repo_router = APIRouter(prefix="/repositories", tags=["repositories"])


@repo_router.get("/")
async def get_repositories():
    return

@repo_router.get("/{repo_url}")
async def get_repository(repo_url: str):
    contributors = set()

    for commit in Repository(repo_url).traverse_commits():
        author_email = commit.author.email.lower().strip()
        contributors.add(author_email)

    engagement = calculate_engagement(repo_url, contributors)
    return engagement

