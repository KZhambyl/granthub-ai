from fastapi import APIRouter, status, Depends, Request
from fastapi.exceptions import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from app.services.grantService import GrantService
from app.db.main import get_session
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from app.services.internshipService import InternshipService
from app.services.scholarshipService import ScholarshipService
from app.auth.dependencies import AccessTokenBearer
import httpx



router = APIRouter()
grant_service = GrantService()
internship_service = InternshipService()
scholarship_service = ScholarshipService()
templates = Jinja2Templates(directory="demo_front/templates")

@router.get("/", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def base(
    request: Request
):  
    return templates.TemplateResponse("base.html", {"request": request})

# Grants

@router.get("/grants", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_all_grants(
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    grants = await grant_service.get_all_grants(session)
    return templates.TemplateResponse("grants.html", {"request": request, "grants": grants})

@router.get("/grants/{grant_id}", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_grant(
    request: Request,
    grant_id: int,
    session: AsyncSession = Depends(get_session)
):
    grant = await grant_service.get_grant(grant_id, session)

    if grant:
        return templates.TemplateResponse("grant_detail.html", {"request": request, "grant": grant})

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grant not found")

# Internships

@router.get("/internships/", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_all_internships(request: Request, session: AsyncSession = Depends(get_session)):
    internships = await internship_service.get_all_internships(session)
    return templates.TemplateResponse("internships.html", {"request": request, "internships": internships})

@router.get("/internships/{internship_id}", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_internship(request: Request, internship_id: int, session: AsyncSession = Depends(get_session)):
    internship = await internship_service.get_internship(internship_id, session)

    if internship:
        return templates.TemplateResponse("internship_detail.html", {"request": request, "internship": internship})

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Internship not found")

# Scholarships

@router.get("/scholarships/", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_all_scholarships(request: Request, session: AsyncSession = Depends(get_session)):
    scholarships = await scholarship_service.get_all_scholarships(session)
    return templates.TemplateResponse("scholarships.html", {"request": request, "scholarships": scholarships})

@router.get("/scholarships/{scholarship_id}", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_scholarship(request: Request, scholarship_id: int, session: AsyncSession = Depends(get_session)):
    scholarship = await scholarship_service.get_scholarship(scholarship_id, session)

    if scholarship:
        return templates.TemplateResponse("scholarship_detail.html", {"request": request, "scholarship": scholarship})

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scholarship not found")

# Auth

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Recommendations

@router.get("/recommendations", response_class=HTMLResponse)
async def recommendations_page(request: Request):
    return templates.TemplateResponse("recommendations.html", {"request": request})

@router.get("/recommendations/data")
async def recommendations_data(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return JSONResponse(status_code=401, content={"detail": "Missing token"})

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "http://127.0.0.1:8000/api/v1/recommendations/",
            headers={"Authorization": auth_header}
        )
    return JSONResponse(status_code=resp.status_code, content=resp.json())