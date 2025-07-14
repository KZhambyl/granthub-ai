from sqlmodel import create_engine, text, SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


async_engine: AsyncEngine = create_async_engine(
    url=settings.DATABASE_URL,
    echo=True,
)

async def init_db():
    async with async_engine.begin() as conn:
        from app.models.baseModel import BaseOpportunity

        await conn.run_sync(SQLModel.metadata.create_all)



async def get_session() -> AsyncSession:
    
    Session = sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with Session() as session:
        yield session