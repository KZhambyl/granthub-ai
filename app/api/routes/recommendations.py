from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.db.main import get_session
from app.auth.dependencies import get_current_user, RoleChecker
from app.auth.models import User
from app.schemes.recommendation import RecommendationCreate, RecommendationRead
from app.services.recommendationService import RecommendationService

router = APIRouter()

check_admin_or_ml = RoleChecker(["admin", "ml_service"])
check_admin = RoleChecker(["admin"])
test_role = RoleChecker(["user"])

recommendation_service = RecommendationService()

@router.get("/")
async def get_user_recommendations(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    recommendations = await recommendation_service.get_recommendations_for_user(current_user.uid, session)
    return {
        "user_id": str(current_user.uid),
        "recommendations": recommendations
    }

@router.post("/", response_model=List[RecommendationRead], status_code=201)
async def create(
    recommendations: List[RecommendationCreate],
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(test_role)  # dev: use test_role; prod: use check_admin_or_ml
):
    return await recommendation_service.create_recommendations(recommendations, session)

@router.delete("/{rec_id}", status_code=204)
async def delete(
    rec_id: UUID,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(check_admin)
):
    try:
        await recommendation_service.delete_recommendation(rec_id, session)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
