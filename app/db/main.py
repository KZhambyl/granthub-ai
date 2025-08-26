# app/db/main.py
from __future__ import annotations

from typing import AsyncIterator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings


# Движок
async_engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
    future=True,
)

# Фабрика асинхронных сессий (доступна и из Celery)
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Инициализация БД (dev only)
async def init_db(dev_create_all: bool = False) -> None:
    async with async_engine.begin() as conn:
        if dev_create_all:
            from app.models import grant, internship, scholarship  # noqa: F401
            await conn.run_sync(SQLModel.metadata.create_all)
        else:
            # Лёгкий тест подключения
            await conn.run_sync(lambda sync_conn: None)


# Зависимость FastAPI
async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


# Закрытие движка вручную
async def dispose_engine() -> None:
    await async_engine.dispose()
