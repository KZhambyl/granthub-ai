from typing import List
from uuid import UUID
from typing import Any, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.recommendation import Recommendation
from app.models.grant import Grant
from app.models.internship import Internship
from app.models.scholarship import Scholarship
from app.schemes.recommendation import RecommendationCreate

type_map = {
    "grant": Grant,
    "internship": Internship,
    "scholarship": Scholarship
}


class RecommendationService:
    async def get_recommendations_for_user(self, user_id: UUID, session: AsyncSession) -> List[dict]:
        statement = select(Recommendation).where(Recommendation.user_id == user_id)
        result = await session.execute(statement)
        recommendations = result.scalars().all()

        grouped_ids: dict[str,List[int]] = {"grant":[],"internship":[],"scholarship":[]}
        for rec in recommendations:
            if rec.item_type in grouped_ids:
                grouped_ids[rec.item_type].append(rec.item_id)

        loaded_items: dict[str, dict[int, Any]] = {}

        for item_type, ids in grouped_ids.items():
            model = type_map.get(item_type)
            if model and ids:
                statement = select(model).where(model.id.in_(ids))
                res = await session.execute(statement)
                items = res.scalars().all()
                loaded_items[item_type] = {item.id: item for item in items}

        items = []
        for rec in recommendations:
            item = loaded_items.get(rec.item_type, {}).get(rec.item_id)
            if item:
                items.append({
                    "type": rec.item_type,
                    "item_id": rec.item_id,
                    "score": rec.score,
                    "source_model": rec.source_model,
                    "data": item
                })

        return items



    async def create_recommendations(
        self,
        data: List[RecommendationCreate],
        session: AsyncSession
    ) -> List[Recommendation]:
        objs = [Recommendation(**rec.model_dump()) for rec in data]
        session.add_all(objs)
        await session.commit()
        for obj in objs:
            await session.refresh(obj)
        return objs


    async def delete_recommendation(self, rec_id: UUID, session: AsyncSession) -> None:
        result = await session.exec(select(Recommendation).where(Recommendation.id == rec_id))
        rec = result.one_or_none()

        if not rec:
            raise Exception("Recommendation not found")

        await session.delete(rec)
        await session.commit()
