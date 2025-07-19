from fastapi import APIRouter
from .grants import router as grants_router
from .scholarships import router as scholarships_router
from .internships import router as internships_router
from .recommendations import router as recommendations_router

router = APIRouter()
router.include_router(grants_router, prefix="/grants", tags=["Grants"])
router.include_router(scholarships_router, prefix="/scholarships", tags=["Scholarships"])
router.include_router(internships_router, prefix="/internships", tags=["Internships"])
router.include_router(recommendations_router, prefix="/recommendations", tags=["Recommendations"])
