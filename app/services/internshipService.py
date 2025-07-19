from sqlmodel.ext.asyncio.session import AsyncSession
from app.schemes import internship
from sqlmodel import select, desc
from app.models.internship import Internship
from datetime import datetime


class InternshipService:
    async def get_all_internships(self, session: AsyncSession):
        statement = select(Internship).order_by(desc(Internship.created_at))

        result = await session.exec(statement)
        
        return result.all()
    
    async def get_internship(self, internship_id:int, session: AsyncSession):
        statement = select(Internship).where(Internship.id == internship_id)

        result = await session.exec(statement)

        internship = result.first()

        if internship:
            return internship
        else:
            return None

    async def create_internship(self, internship_data: internship.InternshipBase ,session: AsyncSession):
        internship_data_dict = internship_data.model_dump()

        internship_data_dict['source_url'] = str(internship_data_dict['source_url'])
        if internship_data_dict.get('image_url'):
            internship_data_dict['image_url'] = str(internship_data_dict['image_url'])

        if internship_data_dict.get('published_at'):
            internship_data_dict['published_at'] = internship_data_dict['published_at'].replace(tzinfo=None)
        if internship_data_dict.get('deadline'):
            internship_data_dict['deadline'] = internship_data_dict['deadline'].replace(tzinfo=None)


        new_internship = Internship(
            **internship_data_dict
        )

        # new_internship.published_at = datetime.strptime(internship_data_dict['published_at'], "%Y-%m-%d")
        # new_internship.deadline = datetime.strptime(internship_data_dict['deadline'], "%Y-%m-%d")

        session.add(new_internship)

        await session.commit()
        
        return new_internship

    async def update_internship(self, internship_id:int, update_data:internship.InternshipUpdate ,session: AsyncSession):
        internship_to_update = await self.get_internship(internship_id, session)

        if internship_to_update is None:
            return None
        
        update_data_dict = update_data.model_dump(exclude_unset=True)  # exclude_unset=True

        for k,v in update_data_dict.items():
            setattr(internship_to_update, k, v)

        await session.commit()

        return internship_to_update
    
    async def delete_internship(self, internship_id: int, session: AsyncSession):
        internship_to_delete = await self.get_internship(internship_id, session)
        
        if internship_to_delete is None:
            return None
        
        await session.delete(internship_to_delete)
        await session.commit()

        return True
            
