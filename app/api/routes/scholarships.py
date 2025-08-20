from fastapi import APIRouter, status, Depends, Response
from fastapi.exceptions import HTTPException
from app.schemes import scholarship
from sqlmodel.ext.asyncio.session import AsyncSession
from app.services.scholarshipService import ScholarshipService
from app.models.scholarship import Scholarship
from typing import List
from app.db.main import get_session
from app.auth.dependencies import RoleChecker

router = APIRouter()
scholarship_service = ScholarshipService()
checker_admin = Depends(RoleChecker(['admin']))


@router.get("/", response_model=List[scholarship.ScholarshipRead], status_code=status.HTTP_200_OK)
async def get_all_scholarships(session: AsyncSession = Depends(get_session)):
    scholarships = await scholarship_service.get_all_scholarships(session)
    return scholarships


@router.post("/", response_model=scholarship.ScholarshipRead, status_code=status.HTTP_201_CREATED, dependencies=[checker_admin])
async def create_a_scholarship(scholarship_data: scholarship.ScholarshipCreate, session: AsyncSession = Depends(get_session)):
    new_scholarship = await scholarship_service.create_scholarship(scholarship_data, session)
    return new_scholarship


@router.get("/{scholarship_id}", response_model=scholarship.ScholarshipRead, status_code=status.HTTP_200_OK)
async def get_scholarship(scholarship_id: int, session: AsyncSession = Depends(get_session)):
    scholarship = await scholarship_service.get_scholarship(scholarship_id, session)

    if scholarship:
        return scholarship

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scholarship not found")


@router.patch("/{scholarship_id}", response_model=scholarship.ScholarshipRead, status_code=status.HTTP_202_ACCEPTED, dependencies=[checker_admin])
async def update_scholarship(scholarship_id: int, update_data: scholarship.ScholarshipUpdate, session: AsyncSession = Depends(get_session)):
    updated_scholarship = await scholarship_service.update_scholarship(scholarship_id, update_data, session)

    if updated_scholarship:
        return updated_scholarship

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scholarship not found")


@router.delete("/{scholarship_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[checker_admin])
async def delete_scholarship(scholarship_id: int, session: AsyncSession = Depends(get_session)):
    success = await scholarship_service.delete_scholarship(scholarship_id, session)

    if success:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail="Scholarship not found")
