from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, desc
from app.schemas import scholarship
from app.models.scholarship import Scholarship
from datetime import datetime


class ScholarshipService:
    async def get_all_scholarships(self, session: AsyncSession):
        statement = select(Scholarship).order_by(desc(Scholarship.created_at))
        result = await session.exec(statement)
        return result.all()
    
    async def get_scholarship(self, scholarship_id: int, session: AsyncSession):
        statement = select(Scholarship).where(Scholarship.id == scholarship_id)
        result = await session.exec(statement)
        scholarship_obj = result.first()
        return scholarship_obj

    async def create_scholarship(self, scholarship_data: scholarship.ScholarshipBase, session: AsyncSession):
        scholarship_data_dict = scholarship_data.model_dump()

        scholarship_data_dict['source_url'] = str(scholarship_data_dict['source_url'])
        if scholarship_data_dict.get('image_url'):
            scholarship_data_dict['image_url'] = str(scholarship_data_dict['image_url'])

        if scholarship_data_dict.get('published_at'):
            scholarship_data_dict['published_at'] = scholarship_data_dict['published_at'].replace(tzinfo=None)
        if scholarship_data_dict.get('deadline'):
            scholarship_data_dict['deadline'] = scholarship_data_dict['deadline'].replace(tzinfo=None)

        new_scholarship = Scholarship(
            **scholarship_data_dict
        )

        # new_scholarship.published_at = datetime.strptime(scholarship_data_dict['published_at'], "%Y-%m-%d")
        # new_scholarship.deadline = datetime.strptime(scholarship_data_dict['deadline'], "%Y-%m-%d")


        session.add(new_scholarship)
        await session.commit()
        return new_scholarship

    async def update_scholarship(self, scholarship_id: int, update_data: scholarship.ScholarshipUpdate, session: AsyncSession):
        scholarship_to_update = await self.get_scholarship(scholarship_id, session)

        if scholarship_to_update is None:
            return None
        
        update_data_dict = update_data.model_dump(exclude_unset=True)

        for key, value in update_data_dict.items():
            setattr(scholarship_to_update, key, value)

        await session.commit()
        return scholarship_to_update

    async def delete_scholarship(self, scholarship_id: int, session: AsyncSession):
        scholarship_to_delete = await self.get_scholarship(scholarship_id, session)
        
        if scholarship_to_delete is None:
            return None
        
        await session.delete(scholarship_to_delete)
        await session.commit()
        return True
