from fastapi import APIRouter, status, Depends, Response, Query, Header
from fastapi.exceptions import HTTPException
from typing import List, Optional, Literal

from sqlmodel.ext.asyncio.session import AsyncSession

from app.schemes import grant
from app.services.grantService import GrantService
from app.db.main import get_session
from app.auth.dependencies import AccessTokenBearer, RoleChecker

router = APIRouter(prefix="/grants", tags=["grants"])

grant_service = GrantService()
access_token_bearer = AccessTokenBearer()

role_checker = Depends(RoleChecker(['admin', 'user']))
checker_admin = Depends(RoleChecker(['admin']))

@router.get("/", response_model=List[grant.GrantRead],
            status_code=status.HTTP_200_OK,
            dependencies=[role_checker])
async def get_all_grants(
    session: AsyncSession = Depends(get_session),
    # Пагинация
    page: int = Query(1, ge=1, description="Номер страницы, начиная с 1"),
    page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    # Фильтры
    q: Optional[str] = Query(None, description="Поиск по title/description"),
    provider: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    deadline_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    deadline_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    # Сортировка
    sort_by: Literal["created_at", "published_at", "deadline"] = Query("created_at"),
    order: Literal["asc", "desc"] = Query("desc"),
    response: Response = None,
):
    """
    Возвращает список грантов с пагинацией/фильтрами/сортировкой.
    Метаданные пагинации кладутся в заголовки X-Total-Count, X-Page, X-Page-Size.
    """
    # делегируем бизнес-логику в сервис (добавь там соответствующие параметры)
    items, total = await grant_service.get_all_grants(
        session=session,
        page=page,
        page_size=page_size,
        q=q,
        provider=provider,
        country=country,
        deadline_from=deadline_from,
        deadline_to=deadline_to,
        sort_by=sort_by,
        order=order,
    )

    # Заголовки пагинации
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page"] = str(page)
    response.headers["X-Page-Size"] = str(page_size)
    return items


@router.post("/", response_model=grant.GrantRead,
             status_code=status.HTTP_201_CREATED,
             dependencies=[checker_admin])
async def create_a_grant(
    grant_data: grant.GrantCreate,
    session: AsyncSession = Depends(get_session),
    _user = Depends(access_token_bearer),
    response: Response = None,
):
    new_grant = await grant_service.create_grant(grant_data, session)
    # Укажем Location на созданный ресурс
    response.headers["Location"] = f"/grants/{new_grant.id}"
    return new_grant


@router.get("/{grant_id}", response_model=grant.GrantRead,
            status_code=status.HTTP_200_OK,
            dependencies=[role_checker])
async def get_grant(grant_id: int, session: AsyncSession = Depends(get_session)):
    item = await grant_service.get_grant(grant_id, session)
    if item:
        return item
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grant not found")


@router.patch("/{grant_id}", response_model=grant.GrantRead,
              status_code=status.HTTP_202_ACCEPTED,
              dependencies=[checker_admin])
async def update_grant(grant_id: int, update_data: grant.GrantUpdate,
                       session: AsyncSession = Depends(get_session)):
    updated = await grant_service.update_grant(grant_id, update_data, session)
    if updated:
        return updated
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grant not found")


@router.delete("/{grant_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[checker_admin])
async def delete_grant(grant_id: int, session: AsyncSession = Depends(get_session)):
    success = await grant_service.delete_grant(grant_id, session)
    if success:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grant not found")