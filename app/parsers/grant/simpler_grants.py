from __future__ import annotations

import asyncio
import re
from datetime import datetime
from typing import Iterable, List, Optional, Tuple, Dict
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from sqlmodel.ext.asyncio.session import AsyncSession

from app.schemes.grant import GrantCreate
from app.services.grantService import GrantService

BASE = "https://simpler.grants.gov"

# Базовый URL выдачи из твоего запроса
BASE_LIST_URL = (
    "https://simpler.grants.gov/search"
    "?utm_source=Grants.gov"
    "&fundingInstrument=grant"
    "&eligibility=individuals,public_and_state_institutions_of_higher_education,"
    "private_institutions_of_higher_education,unrestricted"
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

# утилиты 

def _clean_text(s: Optional[str]) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", s).strip()

def _parse_any_us_date(s: Optional[str]) -> Optional[datetime]:
    """Поддержка форматов вида 'Sep 9, 2025', 'September 9, 2025', '03/21/2023'."""
    if not s:
        return None
    s = _clean_text(s)
    for fmt in ("%b %d, %Y", "%B %d, %Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None

def _extract_first_date_after(label_text: str, haystack: str) -> Optional[datetime]:
    """
    Ищем 'Posted date: Jun 12, 2025' или 'Last Updated: February 26, 2025'
    """
    m = re.search(
        rf"{re.escape(label_text)}\s*:\s*([A-Za-z]{{3,9}}\s+\d{{1,2}},\s+\d{{4}})",
        haystack,
        flags=re.IGNORECASE,
    )
    if m:
        return _parse_any_us_date(m.group(1))
    return None

# парсинг листинга 

def _parse_list_page(html: str) -> List[Dict]:
    """
    Возвращает список элементов:
    {
        'title': str,
        'href': str (absolute),
        'agency': str,
        'close_date': Optional[datetime],
        'posted_at': Optional[datetime],
    }
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", attrs={"data-testid": "table"})
    if not table or not table.tbody:
        return []

    items: List[Dict] = []
    rows = table.tbody.find_all("tr", recursive=False)

    for tr in rows:
        tds = tr.find_all("td", recursive=False)
        if len(tds) < 4:
            continue

        # close date — в первом td
        close_text = _clean_text(tds[0].get_text(" ", strip=True))
        close_dt = _parse_any_us_date(close_text)

        # третий td (index 2): содержит ссылку и заголовок
        a = tds[2].find("a", href=True)
        if not a:
            continue
        title = _clean_text(a.get_text(" ", strip=True))
        href = urljoin(BASE, a["href"])

        # четвёртый td (index 3): agency + "Posted date: ..."
        agency_block_text = _clean_text(tds[3].get_text(" ", strip=True))
        # agency — это всё до "Posted date"
        agency = agency_block_text.split("Posted date")[0].strip(" :") or "Unknown agency"
        posted_at = _extract_first_date_after("Posted date", agency_block_text)

        items.append(
            {
                "title": title,
                "href": href,
                "agency": agency,
                "close_date": close_dt,
                "posted_at": posted_at,
            }
        )

    return items

# парсинг карточки 

def _extract_description_from_detail(soup: BeautifulSoup) -> str:
    """
    В блоке data-testid="opportunity-description" обычно:
      [header div с H2] [div с основным текстом] [div data-testid="toggled-content-container"] [кнопка Show full...]
    Собираем основной + "toggled" куски.
    """
    container = soup.find("div", attrs={"data-testid": "opportunity-description"})
    if not container:
        return ""

    parts: List[str] = []

    # Берём все дочерние div'ы этого контейнера и пропускаем header-контейнер с H2 и кнопку.
    for child in container.find_all("div", recursive=False):
        # пропускаем шапку с заголовком "Description"
        if child.find("h2"):
            continue
        # пропускаем кнопки раскрытия
        if child.get("data-testid") == "content-display-toggle":
            continue
        text = _clean_text(child.get_text(" ", strip=True))
        if text:
            parts.append(text)

    # убираем мусор типа "Show full description"
    text = "\n\n".join(parts)
    text = re.sub(r"Show full description$", "", text, flags=re.IGNORECASE).strip()
    return text

def _extract_deadline_from_detail(soup: BeautifulSoup) -> Optional[datetime]:
    """
    В сайдбаре виджет 'Closing: September 9, 2025'
    """
    box = soup.find("div", attrs={"data-testid": "opportunity-status-widget"})
    if not box:
        return None
    txt = _clean_text(box.get_text(" ", strip=True))
    m = re.search(r"Closing:\s*([A-Za-z]{3,9}\s+\d{1,2},\s+\d{4})", txt, re.IGNORECASE)
    if m:
        return _parse_any_us_date(m.group(1))
    return None

def _extract_agency_from_detail(soup: BeautifulSoup, fallback: str) -> str:
    """
    Вверху страницы есть p с 'Agency: ...'
    """
    for p in soup.find_all("p"):
        t = _clean_text(p.get_text(" ", strip=True))
        if "Agency:" in t:
            # всё после 'Agency:'
            return _clean_text(t.split("Agency:", 1)[1])
    return fallback

def _extract_posted_date_from_detail(soup: BeautifulSoup, fallback: Optional[datetime]) -> Optional[datetime]:
    # сначала пробуем "Posted date" в разделе History
    whole = _clean_text(soup.get_text(" ", strip=True))
    posted = _extract_first_date_after("Posted date", whole)
    if posted:
        return posted
    # иначе можно взять "Last Updated"
    last_updated = _extract_first_date_after("Last Updated", whole)
    return posted or last_updated or fallback

async def _fetch_detail_page(client: httpx.AsyncClient, url: str) -> Tuple[str, Optional[datetime], Optional[datetime], str]:
    """
    Возвращает (description, deadline, posted_at, agency_from_detail)
    """
    r = await client.get(url, timeout=40)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    description = _extract_description_from_detail(soup)
    deadline = _extract_deadline_from_detail(soup)
    agency = _extract_agency_from_detail(soup, fallback="Unknown agency")
    posted_at = _extract_posted_date_from_detail(soup, fallback=None)
    return description, deadline, posted_at, agency

def _to_grant_create(
    title: str,
    description: str,
    source_url: str,
    deadline: Optional[datetime],
    published_at: Optional[datetime],
    provider: str,
) -> GrantCreate:
    return GrantCreate(
        title=title.strip() or "Untitled",
        description=(description or "").strip(),
        source_url=source_url,
        deadline=deadline,
        published_at=published_at,
        country="USA",
        region=None,
        language="en",
        provider=(provider or "Unknown agency").strip(),
        image_url=None,
    )

# основной импортёр 

async def fetch_grants_from_simpler(
    session: AsyncSession,
    pages: int = 1,
    start_page: int = 1,
    throttle_sec: float = 0.0,
) -> List[int]:
    """
    Проходит по выдаче Simpler.Grants.gov, парсит и создаёт записи через GrantService.
    Возвращает список ID созданных грантов.
    """
    created_ids: List[int] = []
    grant_service = GrantService()

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        for page in range(start_page, start_page + pages):
            list_url = BASE_LIST_URL if page == 1 else f"{BASE_LIST_URL}&page={page}"
            resp = await client.get(list_url, timeout=40)
            resp.raise_for_status()

            items = _parse_list_page(resp.text)
            if not items:
                # Нечего парсить — идём дальше
                if throttle_sec:
                    await asyncio.sleep(throttle_sec)
                continue

            # Параллельно тянем карточки
            tasks = [asyncio.create_task(_fetch_detail_page(client, it["href"])) for it in items]
            details = await asyncio.gather(*tasks, return_exceptions=True)

            for it, det in zip(items, details):
                if isinstance(det, Exception):
                    # Если карточка упала — сохраним хотя бы из листинга
                    description, deadline, posted_at, agency_from_detail = "", it["close_date"], it["posted_at"], it["agency"]
                else:
                    description, deadline_d, posted_at_d, agency_from_detail = det
                    # приоритет: deadline из карточки > из листинга; published_at: posted из карточки > из листинга
                    deadline = deadline_d or it["close_date"]
                    posted_at = posted_at_d or it["posted_at"]

                provider = agency_from_detail or it["agency"]

                grant_obj = _to_grant_create(
                    title=it["title"],
                    description=description,
                    source_url=it["href"],  # можно заменить на Grants.gov link, но этот стабильно работает
                    deadline=deadline,
                    published_at=posted_at,
                    provider=provider,
                )

                try:
                    new_grant = await grant_service.create_grant(grant_obj, session)
                    created_ids.append(new_grant.id)
                except Exception:
                    # На случай уникальности по title+source_url и т.п. — просто пропустим
                    pass

            if throttle_sec:
                await asyncio.sleep(throttle_sec)

    return created_ids


# Удобная обвязка для ручного запуска из консоли:
async def import_simpler_grants(pages: int = 1, start_page: int = 1) -> List[int]:
    """
    Пример: asyncio.run(import_simpler_grants(pages=2))
    """
    from app.db.main import get_session
    async for s in get_session():
        return await fetch_grants_from_simpler(s, pages=pages, start_page=start_page)
