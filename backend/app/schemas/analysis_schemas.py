from datetime import datetime
from typing import Any
from pydantic import BaseModel, HttpUrl, ConfigDict

from app.models.analyseModel import AnalysisStatus


class AnalysisCreate(BaseModel):
    repo_url: HttpUrl


class AnalysisResponse(BaseModel):
    id: str
    repo_url: str
    status: AnalysisStatus
    metrics_result: dict[str, Any] | None = None
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)