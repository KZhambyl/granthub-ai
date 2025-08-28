# app/api/routes/etl_simpler_grants.py
from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.main import get_session
from app.parsers.grant.simpler_grants import fetch_grants_from_simpler

router = APIRouter(prefix="/etl", tags=["etl"])

@router.post("/simpler-grants/run")
async def run_simpler_grants(
    pages: int = Query(1, ge=1, le=25, description="Сколько страниц листинга обойти"),
    start_page: int = Query(1, ge=1, description="С какой страницы начинать (обычно 1)"),
    throttle_sec: float = Query(0.0, ge=0.0, le=5.0, description="Пауза между страницами (сек)"),
    session: AsyncSession = Depends(get_session),
):
    """
    ETL из Simpler.Grants.gov:
    - проходит страницы выдачи,
    - ходит в карточки,
    - сохраняет гранты через GrantService,
    - возвращает список созданных ID.
    """
    try:
        ids = await fetch_grants_from_simpler(
            session=session,
            pages=pages,
            start_page=start_page,
            throttle_sec=throttle_sec,
        )
        return {
            "source": "simpler.grants.gov",
            "pages": pages,
            "start_page": start_page,
            "throttle_sec": throttle_sec,
            "inserted": len(ids),
            "ids": ids,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": e.__class__.__name__, "message": str(e)},
        )
