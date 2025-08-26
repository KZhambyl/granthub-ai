# app/api/routes/etl_scholarships.py
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.main import get_session
from app.parsers.scholarship.internationalscholarships import (
    fetch_scholarships_from_internationalscholarships,
)

router = APIRouter(prefix="/etl", tags=["etl"])

@router.post("/intl-scholarships/run")
async def run_intl_scholarships(
    details: int = Query(128, description="AwardSearch[details] (страна/национальность)"),
    limit: int = Query(10, ge=1, le=500, description="Сколько карточек всего забрать (max_items)"),
    pages: int = Query(1, ge=1, le=25, description="Сколько страниц листинга обойти (max_pages)"),
    per_page: int = Query(40, ge=5, le=1000, description="Сколько рядов на странице листинга (per-page)"),
    dry_run: bool = Query(False, description="Не писать в БД, только скачать/распарсить"),
    skip_past_years: bool = Query(True, description="Пропускать карточки с годом < текущего"),
    session: AsyncSession = Depends(get_session),
):
    try:
        result = await fetch_scholarships_from_internationalscholarships(
            session=session,
            details=details,
            max_items=limit,
            max_pages=pages,
            per_page=per_page,
            dry_run=dry_run,
            skip_past_years=skip_past_years,
        )
        if dry_run:
            return {"dry_run": True, "items": result, "count": len(result)}
        return {"inserted": len(result), "ids": result}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": e.__class__.__name__, "message": str(e)})
