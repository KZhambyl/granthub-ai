from fastapi import APIRouter, status, Depends, Response
from fastapi.exceptions import HTTPException
from app.schemas import grant
from sqlmodel.ext.asyncio.session import AsyncSession
from app.services.grantService import GrantService
from app.models.grant import Grant
from typing import List
from app.db.main import get_session

router = APIRouter()
grant_service = GrantService()


@router.get("/", response_model=List[grant.GrantRead], status_code=status.HTTP_200_OK)
async def get_all_grants(session:AsyncSession = Depends(get_session)):
    grants = await grant_service.get_all_grants(session)
    return grants


@router.post("/", response_model=grant.GrantRead, status_code=status.HTTP_201_CREATED)
async def create_a_grant(grant_data:grant.GrantCreate, session: AsyncSession = Depends(get_session)):
    new_grant = await grant_service.create_grant(grant_data, session)

    return new_grant


@router.get("/{grant_id}", response_model=grant.GrantRead, status_code=status.HTTP_200_OK)
async def get_grant(grant_id: int, session: AsyncSession = Depends(get_session)):
    grant = await grant_service.get_grant(grant_id, session)

    if grant:
        return grant

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grant not found")


@router.patch("/{grant_id}", response_model=grant.GrantRead, status_code=status.HTTP_202_ACCEPTED)
async def update_grant(grant_id: int, update_data: grant.GrantUpdate, session: AsyncSession = Depends(get_session)):
    updated_grant = await grant_service.update_grant(grant_id, update_data, session)

    if updated_grant:
        return updated_grant
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grant not found")


@router.delete("/{grant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_grant(grant_id: int, session: AsyncSession = Depends(get_session)):
    success = await grant_service.delete_grant(grant_id, session)

    if success:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail="Grant not found")