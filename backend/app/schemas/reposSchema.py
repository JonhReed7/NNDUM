from pydantic import BaseModel


class RepositorySchema(BaseModel):
    repo_url: str
    commits_count: int
    code_churn: int
    score: float