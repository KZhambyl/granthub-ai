from sqlmodel.ext.asyncio.session import AsyncSession
from app.schemas import grant
from sqlmodel import select, desc
from app.models.grant import Grant
from datetime import datetime


class GrantService:
    async def get_all_grants(self, session: AsyncSession):
        statement = select(Grant).order_by(desc(Grant.created_at))

        result = await session.exec(statement)
        
        return result.all()
    
    async def get_grant(self, grant_id:int, session: AsyncSession):
        statement = select(Grant).where(Grant.id == grant_id)

        result = await session.exec(statement)

        grant = result.first()

        if grant:
            return grant
        else:
            return None

    async def create_grant(self, grant_data: grant.GrantBase ,session: AsyncSession):
        grant_data_dict = grant_data.model_dump()

        grant_data_dict['source_url'] = str(grant_data_dict['source_url'])
        if grant_data_dict.get('image_url'):
            grant_data_dict['image_url'] = str(grant_data_dict['image_url'])

        if grant_data_dict.get('published_at'):
            grant_data_dict['published_at'] = grant_data_dict['published_at'].replace(tzinfo=None)
        if grant_data_dict.get('deadline'):
            grant_data_dict['deadline'] = grant_data_dict['deadline'].replace(tzinfo=None)

        new_grant = Grant(
            **grant_data_dict
        )
        
        # new_grant.published_at = datetime.strptime(grant_data_dict['published_at'], "%Y-%m-%d")
        # new_grant.deadline = datetime.strptime(grant_data_dict['deadline'], "%Y-%m-%d")

        session.add(new_grant)

        await session.commit()
        
        return new_grant

    async def update_grant(self, grant_id:int, update_data:grant.GrantUpdate ,session: AsyncSession):
        grant_to_update = await self.get_grant(grant_id, session)

        if grant_to_update is None:
            return None
        
        update_data_dict = update_data.model_dump(exclude_unset=True)  # exclude_unset=True

        for k,v in update_data_dict.items():
            setattr(grant_to_update, k, v)

        await session.commit()

        return grant_to_update
    
    async def delete_grant(self, grant_id: int, session: AsyncSession):
        grant_to_delete = await self.get_grant(grant_id, session)
        
        if grant_to_delete is None:
            return None
        
        await session.delete(grant_to_delete)
        await session.commit()

        return True
            
