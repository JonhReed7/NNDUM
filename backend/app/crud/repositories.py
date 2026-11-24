import jwt
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.analyseModel import Analyse
from app.models.user_model import User
from app.schemas.analysis_schemas import AnalysisResponse, AnalysisCreate

from app.services.analyzer import run_repository_analysis

analysis_router = APIRouter(prefix="/analyses", tags=["Analyses"])


@analysis_router.post(
    "/",
    response_model=AnalysisResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_repository_analysis(
    payload: AnalysisCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    github_token = None
    if current_user:
        github_token = current_user.github_access_token

    # РЎРѕР·РґР°РµРј Р·Р°РїРёСЃСЊ РІ Р‘Р” СЃРѕ СЃС‚Р°С‚СѓСЃРѕРј PENDING
    new_analysis = Analyse(
        repo_url=str(payload.repo_url),
        user_id=current_user.id,
    )
    db.add(new_analysis)
    await db.commit()
    await db.refresh(new_analysis)

    # РЎС‚Р°РІРёРј С‚СЏР¶РµР»СѓСЋ Р·Р°РґР°С‡Сѓ РІ С„РѕРЅ
    background_tasks.add_task(
        run_repository_analysis,
        analysis_id=new_analysis.id,
        github_token=github_token,
    )

    # РњРіРЅРѕРІРµРЅРЅРѕ РІРѕР·РІСЂР°С‰Р°РµРј 202 Accepted Рё ID Р·Р°РґР°С‡Рё
    return new_analysis


@analysis_router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis_status(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
):
    analysis = await db.scalar(select(Analyse).where(Analyse.id == analysis_id))
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis task not found",
        )
    return analysis