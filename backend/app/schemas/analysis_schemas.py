from datetime import datetime
from pydantic import BaseModel, HttpUrl, ConfigDict

from app.models.analyse_model import AnalysisStatus
from app.schemas.metrics_schemas import AnalysisResult


class AnalysisCreate(BaseModel):
    repo_url: HttpUrl


class AnalysisResponse(BaseModel):
    id: str
    repo_url: str
    status: AnalysisStatus
    metrics_result: AnalysisResult | None = None
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
