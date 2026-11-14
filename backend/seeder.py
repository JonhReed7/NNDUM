# seed.py
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import AsyncSessionLocal, engine, Base
from app.models.reposModel import Repository


async def seed_database():
    # Создаем таблицы на случай, если они еще не созданы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    test_data = [
        Repository(
            repo_url="https://sfera.code/t1/project-alpha",
            commits_count=42,
            code_churn=1520,
            score=88.5
        ),
        Repository(
            repo_url="https://sfera.code/t1/backend-core",
            commits_count=128,
            code_churn=4300,
            score=94.2
        ),
        Repository(
            repo_url="https://sfera.code/t1/frontend-ui",
            commits_count=75,
            code_churn=2100,
            score=76.0
        ),
        Repository(
            repo_url="https://sfera.code/t1/auth-service",
            commits_count=19,
            code_churn=650,
            score=65.4
        )
    ]

    async with AsyncSessionLocal() as session:
        async with session.begin():
            for item in test_data:
                session.add(item)
        await session.commit()

    print("База данных успешно заполнена тестовыми данными!")


if __name__ == "__main__":
    asyncio.run(seed_database())