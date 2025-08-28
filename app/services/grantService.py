from __future__ import annotations
from typing import Optional, Tuple, List
from datetime import datetime, date

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, desc, asc
from sqlalchemy import func, or_, and_

from app.schemes import grant as grant_schema
from app.models.grant import Grant


def _parse_date(value: Optional[str | date | datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    # ожидаем 'YYYY-MM-DD'
    return datetime.strptime(str(value), "%Y-%m-%d")


_SORT_MAP = {
    "created_at": Grant.created_at,
    "published_at": Grant.published_at,
    "deadline": Grant.deadline,
}


class GrantService:
    async def get_all_grants(
        self,
        session: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        q: Optional[str] = None,
        provider: Optional[str] = None,
        country: Optional[str] = None,
        deadline_from: Optional[str] = None,
        deadline_to: Optional[str] = None,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> Tuple[List[Grant], int]:
        # Базовый запрос
        stmt = select(Grant)

        # Фильтр поиска по тексту
        if q:
            like = f"%{q}%"
            stmt = stmt.where(
                or_(
                    Grant.title.ilike(like),
                    Grant.description.ilike(like),
                )
            )

        # Фильтры по полям
        if provider:
            stmt = stmt.where(Grant.provider.ilike(f"%{provider}%"))
        if country:
            stmt = stmt.where(Grant.country.ilike(f"%{country}%"))

        df = _parse_date(deadline_from)
        dt = _parse_date(deadline_to)
        if df and dt:
            stmt = stmt.where(and_(Grant.deadline >= df, Grant.deadline <= dt))
        elif df:
            stmt = stmt.where(Grant.deadline >= df)
        elif dt:
            stmt = stmt.where(Grant.deadline <= dt)

        # Подсчёт total до пагинации
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.exec(count_stmt)).one()

        # Сортировка
        sort_col = _SORT_MAP.get(sort_by, Grant.created_at)
        order_by = desc(sort_col) if order.lower() == "desc" else asc(sort_col)
        stmt = stmt.order_by(order_by)

        # Пагинация
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await session.exec(stmt)
        items = result.all()
        return items, total

    async def get_grant(self, grant_id: int, session: AsyncSession) -> Optional[Grant]:
        stmt = select(Grant).where(Grant.id == grant_id)
        result = await session.exec(stmt)
        return result.first()

    async def create_grant(self, grant_data: grant_schema.GrantBase, session: AsyncSession) -> Grant:
        data = grant_data.model_dump()

        # приведение типов/таймзоны
        data["source_url"] = str(data["source_url"])
        if data.get("image_url"):
            data["image_url"] = str(data["image_url"])

        if data.get("published_at"):
            data["published_at"] = _parse_date(data["published_at"])
        if data.get("deadline"):
            data["deadline"] = _parse_date(data["deadline"])

        title = data.get("title", "").strip()
        source_url = data.get("source_url", "").strip()

        # Idempotency: не создаём дубль по (title, source_url)
        dup_stmt = select(Grant).where(
            and_(Grant.title == title, Grant.source_url == source_url)
        )
        dup = (await session.exec(dup_stmt)).first()
        if dup:
            # можно обновить существующую запись «мягко», если нужно
            return dup

        new_grant = Grant(**data)
        session.add(new_grant)
        await session.commit()
        await session.refresh(new_grant)
        return new_grant

    async def update_grant(
        self, grant_id: int, update_data: grant_schema.GrantUpdate, session: AsyncSession
    ) -> Optional[Grant]:
        grant_to_update = await self.get_grant(grant_id, session)
        if grant_to_update is None:
            return None

        data = update_data.model_dump(exclude_unset=True)

        # нормализуем даты, если пришли как строки
        if "published_at" in data:
            data["published_at"] = _parse_date(data["published_at"])
        if "deadline" in data:
            data["deadline"] = _parse_date(data["deadline"])

        for k, v in data.items():
            setattr(grant_to_update, k, v)

        grant_to_update.updated_at = datetime.utcnow()

        await session.commit()
        await session.refresh(grant_to_update)
        return grant_to_update

    async def delete_grant(self, grant_id: int, session: AsyncSession) -> bool:
        grant_to_delete = await self.get_grant(grant_id, session)
        if grant_to_delete is None:
            return None
        await session.delete(grant_to_delete)
        await session.commit()
        return True
