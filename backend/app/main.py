from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn
from starlette.middleware.cors import CORSMiddleware

from app.crud.repositories import analysis_router
from app.crud.users import user_router
from app.db.base import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):

    from app.models import user_model, teamModel, teamMemberModel, projectModel, sprintModel


    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(analysis_router)


@app.get("/health")
async def get_status():
    return {"status": "ok"}


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)