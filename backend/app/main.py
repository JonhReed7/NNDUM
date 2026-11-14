from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn
from starlette.middleware.cors import CORSMiddleware

from crud.users import user_router
from db.base import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # from app.models.reposModel import Repository
    # Base.metadata.drop_all(engine)
    # Base.metadata.create_all(engine)

    from models.userModel import User

    async with engine.begin() as conn:
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
@app.get("/health")
async def get_status():
    return {"status": "ok"}


@app.get("/repositories")
async def get_repositories():
    return {"id": 1}


@app.get("/repositories/{repository_id}")
async def get_repository(repository_id: int):
    return {"id": 1}








if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)