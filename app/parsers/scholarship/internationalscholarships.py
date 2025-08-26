from __future__ import annotations
import asyncio
import re
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import urljoin, quote_plus

import httpx
from bs4 import BeautifulSoup, Tag
from sqlmodel.ext.asyncio.session import AsyncSession

from app.schemes.scholarship import ScholarshipCreate
from app.services.scholarshipService import ScholarshipService

BASE = "https://www.internationalscholarships.com"
LIST_PRIMARY = "/scholarships"  # нормализованный листинг

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

MONTHS = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

# utils

def _clean_text(x: str | None) -> str:
    if not x:
        return ""
    return re.sub(r"\s+", " ", x).strip()

def _abs(url: str) -> str:
    return url if url.startswith("http") else urljoin(BASE, url)

def _nearest_future_date(month: int, day: int) -> Optional[datetime]:
    now = datetime.now(timezone.utc).astimezone().replace(tzinfo=None)
    year = now.year
    try:
        candidate = datetime(year, month, day)
    except ValueError:
        return None
    if candidate < now:
        try:
            candidate = datetime(year + 1, month, day)
        except ValueError:
            return None
    return candidate

def _parse_human_date(s: str) -> Optional[datetime]:
    """
    Поддерживает:
      - 'Deadline: October 15, 2025'
      - '15 October 2025'
      - 'Oct 31' / '31 Oct' (без года → ближайшее будущее)
      - '12/31/2025'
      - 'Varies/Open/Rolling/Until filled' -> None
    """
    if not s:
        return None
    txt = s.strip()
    if re.search(r"\b(varies|open|ongoing|rolling|until\s+filled)\b", txt, re.I):
        return None

    # убрать префиксы (Deadline: ...)
    txt = re.sub(r"(?i)^.*deadline:\s*", "", txt).strip()

    # Month Day, Year  |  Month Day Year
    m = re.search(r"(?i)\b([A-Za-z]{3,9})\s+(\d{1,2})(?:st|nd|rd|th)?(?:,)?\s+(\d{4})\b", txt)
    if m:
        month = MONTHS.get(m.group(1).lower())
        day = int(m.group(2))
        year = int(m.group(3))
        if month:
            try:
                return datetime(year, month, day)
            except ValueError:
                return None

    # Day Month Year
    m = re.search(r"(?i)\b(\d{1,2})\s+([A-Za-z]{3,9})(?:,)?\s+(\d{4})\b", txt)
    if m:
        day = int(m.group(1))
        month = MONTHS.get(m.group(2).lower())
        year = int(m.group(3))
        if month:
            try:
                return datetime(year, month, day)
            except ValueError:
                return None

    # MM/DD/YYYY
    m = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", txt)
    if m:
        mm, dd, yyyy = map(int, m.groups())
        try:
            return datetime(yyyy, mm, dd)
        except ValueError:
            return None

    # Month Day (без года)
    m = re.search(r"(?i)\b([A-Za-z]{3,9})\s+(\d{1,2})(?:st|nd|rd|th)?\b", txt)
    if m:
        month = MONTHS.get(m.group(1).lower())
        day = int(m.group(2))
        if month:
            return _nearest_future_date(month, day)

    # Day Month (без года)
    m = re.search(r"(?i)\b(\d{1,2})\s+([A-Za-z]{3,9})\b", txt)
    if m:
        day = int(m.group(1))
        month = MONTHS.get(m.group(2).lower())
        if month:
            return _nearest_future_date(month, day)

    return None

def _text_h4_value_block(container: Tag, label_contains: list[str]) -> Optional[str]:
    """
    На карточке поля идут парами <h4>Label</h4><p>Value</p>.
    Ищем h4 по подстроке и забираем текст следующего p.
    """
    for h4 in container.select("h4"):
        lab = _clean_text(h4.get_text(" ", strip=True)).lower()
        if any(kw in lab for kw in label_contains):
            p = h4.find_next_sibling("p")
            if p:
                return _clean_text(p.get_text(" ", strip=True))
    return None

def _normalize_list_url(details: int, per_page: int = 40, page: int = 1) -> str:
    """Всегда строим URL на новый листинг /scholarships с нужными параметрами."""
    params = [
        ("AwardSearch[details]", str(details)),
        ("page", str(page)),
        ("per-page", str(per_page)),
    ]
    query = "&".join([f"{k}={quote_plus(v)}" for k, v in params])
    return f"{BASE}{LIST_PRIMARY}?{query}"

# listing parsers

def _parse_listing(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    items: list[dict] = []

    for a in soup.select('table.table.table-v2 tbody tr td:nth-of-type(1) a[href^="/scholarships/"]'):
        href = (a.get("href") or "").strip()
        title = _clean_text(a.get_text(" ", strip=True)) or "Untitled"
        if href:
            items.append({"title": title, "url": _abs(href)})

    if not items:
        # fallback
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith("/scholarships/"):
                title = _clean_text(a.get_text(" ", strip=True)) or "Untitled"
                items.append({"title": title, "url": _abs(href)})

    # dedup
    seen = set()
    uniq: list[dict] = []
    for it in items:
        if it["url"] not in seen:
            uniq.append(it)
            seen.add(it["url"])
    return uniq

def _next_page_url(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "html.parser")
    active = soup.select_one("ul.pagination li.page-item.active")
    if active:
        nxt = active.find_next_sibling("li")
        if nxt:
            a = nxt.find("a", class_="page-link")
            if a and a.get("href"):
                return _abs(a["href"])
    # fallback
    a = soup.select_one("li.pager-next a.page-link")
    if a and a.get("href"):
        return _abs(a["href"])
    return None

# detail helpers

def _extract_section_text(desc_wrap: Tag, heading_text: str) -> str:
    """
    Берём ТОЛЬКО текст после нужного <h2> до следующего <h2>.
    Возвращаем «плоский» текст (параграфы, br, списки — сведены к пробелам).
    """
    if not desc_wrap:
        return ""
    # найдём <h2> с нужным заголовком
    h2 = None
    for h in desc_wrap.select("h2"):
        if _clean_text(h.get_text()).lower() == heading_text.lower():
            h2 = h
            break
    if not h2:
        return ""

    chunks: list[str] = []
    node = h2.next_sibling
    while node:
        if isinstance(node, Tag) and node.name == "h2":
            break  # дошли до следующей секции
        # собираем из p, li, br и просто текста
        if isinstance(node, Tag):
            # списки
            if node.name in ("ul", "ol"):
                for li in node.find_all("li"):
                    chunks.append(_clean_text(li.get_text(" ", strip=True)))
            # параграфы и прочее блочное
            elif node.name in ("p", "div"):
                chunks.append(_clean_text(node.get_text(" ", strip=True)))
            # просто текст внутри
            else:
                chunks.append(_clean_text(node.get_text(" ", strip=True)))
        else:
            # NavigableString/прочий текст
            text = _clean_text(str(node))
            if text:
                chunks.append(text)
        node = node.next_sibling

    text = _clean_text(" ".join([c for c in chunks if c]))
    return text

def _pick_level(text: str) -> Optional[str]:
    t = text.lower()
    levels = []

    if "phd" in t or "doctoral" in t:
        levels.append("phd")
    if "master" in t or "graduate" in t:
        levels.append("master")
    if "bachelor" in t or "undergraduate" in t:
        levels.append("bachelor")

    # Если нашли хоть один уровень, возвращаем их как строку, разделённую запятыми
    if levels:
        return ", ".join(levels)

    return None


# detail parser

def _parse_detail(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    # title
    h1 = soup.select_one("h1.title, h1, .page-title, .title")
    title = _clean_text(h1.get_text(" ", strip=True)) if h1 else "Untitled"

    # provider/author
    author = soup.select_one(".author")
    provider = _clean_text(author.get_text(" ", strip=True)) if author else "InternationalScholarships.com"

    # блок с описанием
    desc_wrap = soup.select_one(".award-title .award-description")

    # берём строго две секции: Description и Other Criteria (если есть)
    desc_text = _extract_section_text(desc_wrap, "Description")
    other_text = _extract_section_text(desc_wrap, "Other Criteria")
    if desc_text and other_text:
        description = f"Description: {desc_text}\nOther Criteria: {other_text}"
    else:
        description = desc_text or other_text or ""

    # пары <h4>…</h4><p>…</p>
    deadline_txt = _text_h4_value_block(soup, ["deadline"])
    deadline = _parse_human_date(deadline_txt or "")

    host_countries = _text_h4_value_block(
        soup,
        ["you must be studying in", "host countries", "country of study", "You must be from one of the following countries"]
    )
    country_val = _clean_text(host_countries) if host_countries else None
    country = None if (country_val and re.search(r"\bunrestricted\b", country_val, re.I)) else country_val

    # эвристика уровня
    level = _pick_level(" ".join([title, description]))

    return {
        "title": title,
        "description": description,
        "provider": provider,
        "deadline": deadline,
        "country": country,
        "source_url": url,
        "language": "en",
        "region": None,
        "published_at": None,
        "image_url": None,
        "level": level,
    }

# entrypoint

async def fetch_scholarships_from_internationalscholarships(
    session: AsyncSession,
    details: int = 128,
    max_items: int = 20,
    max_pages: int = 1,
    per_page: int = 40,
    dry_run: bool = False,
    skip_past_years: bool = True,
) -> list[int] | list[str]:
    """
    Качаем листинг (/scholarships), обходим карточки и сохраняем.
    Возвращаем список id вставленных записей, либо (в dry_run) список "title :: url".
    """
    service = ScholarshipService()
    created: List[int] = []
    preview: List[str] = []

    next_url = _normalize_list_url(details=details, per_page=per_page, page=1)

    async with httpx.AsyncClient(timeout=30, headers=HEADERS) as client:
        grabbed = 0
        for _ in range(max_pages):
            r = await client.get(next_url)
            r.raise_for_status()

            items = _parse_listing(r.text)
            if not items:
                # на всякий — сохраним дамп
                try:
                    with open("intl_list_dump.html", "w", encoding="utf-8") as f:
                        f.write(r.text[:200_000])
                except Exception:
                    pass
                break

            remain = max_items - grabbed
            if remain <= 0:
                break
            batch = items[:remain]
            grabbed += len(batch)

            async def fetch_one(u: str) -> tuple[str, str] | Exception:
                try:
                    await asyncio.sleep(0.25)
                    resp = await client.get(u)
                    resp.raise_for_status()
                    return u, resp.text
                except Exception as e:
                    return e

            pages = await asyncio.gather(
                *(asyncio.create_task(fetch_one(it["url"])) for it in batch),
                return_exceptions=True
            )

            for p in pages:
                if isinstance(p, Exception) or not isinstance(p, tuple):
                    continue

                url, html = p
                data = _parse_detail(html, url)

                # фильтр по году в title — если указан только прошедший год, пропускаем
                if skip_past_years:
                    now_year = datetime.now().year
                    years = [int(y) for y in re.findall(r"\b((?:19|20)\d{2})\b", data["title"])]
                    if years and max(years) < now_year:
                        continue

                if dry_run:
                    preview.append(f'{data["title"]} :: {url}')
                    continue

                dto = ScholarshipCreate(
                    title=data["title"],
                    description=data["description"],
                    source_url=data["source_url"],
                    deadline=data["deadline"],
                    published_at=data["published_at"],
                    country=data["country"],
                    region=data["region"],
                    language=data["language"],
                    provider=data["provider"],
                    image_url=data["image_url"],
                    level=data["level"],
                )
                try:
                    obj = await service.create_scholarship(dto, session)
                    created.append(obj.id)
                except Exception:
                    # дубль/уникальный индекс — пропускаем
                    continue

            if grabbed >= max_items:
                break

            nxt = _next_page_url(r.text)
            if not nxt:
                break
            next_url = nxt

    return preview if dry_run else created
