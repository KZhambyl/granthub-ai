from fastapi import APIRouter, status, Depends, Response
from fastapi.exceptions import HTTPException
from app.schemas import internship
from sqlmodel.ext.asyncio.session import AsyncSession
from app.services.internshipService import InternshipService
from app.models.internship import Internship
from typing import List
from app.db.main import get_session

router = APIRouter()
internship_service = InternshipService()


@router.get("/", response_model=List[internship.InternshipRead], status_code=status.HTTP_200_OK)
async def get_all_internships(session: AsyncSession = Depends(get_session)):
    internships = await internship_service.get_all_internships(session)
    return internships


@router.post("/", response_model=internship.InternshipRead, status_code=status.HTTP_201_CREATED)
async def create_an_internship(internship_data: internship.InternshipCreate, session: AsyncSession = Depends(get_session)):
    new_internship = await internship_service.create_internship(internship_data, session)
    return new_internship


@router.get("/{internship_id}", response_model=internship.InternshipRead, status_code=status.HTTP_200_OK)
async def get_internship(internship_id: int, session: AsyncSession = Depends(get_session)):
    internship = await internship_service.get_internship(internship_id, session)

    if internship:
        return internship

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Internship not found")


@router.patch("/{internship_id}", response_model=internship.InternshipRead, status_code=status.HTTP_202_ACCEPTED)
async def update_internship(internship_id: int, update_data: internship.InternshipUpdate, session: AsyncSession = Depends(get_session)):
    updated_internship = await internship_service.update_internship(internship_id, update_data, session)

    if updated_internship:
        return updated_internship
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Internship not found")


@router.delete("/{internship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_internship(internship_id: int, session: AsyncSession = Depends(get_session)):
    success = await internship_service.delete_internship(internship_id, session)

    if success:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail="Internship not found")
