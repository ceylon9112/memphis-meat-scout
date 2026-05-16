"""
Whole Foods Market weekly sale scraper.

Source: iweeklyads.com/whole-foods-ad-specials/ — a weekly-updated aggregator
page that pulls highlighted items from the Whole Foods circular.

Coverage: whichever items WF features in their weekly ad summary (3–20 items/week).
Prices are store-specific (Memphis/Germantown stores generally match national WF pricing).
Items labelled "per lb" are extracted with per_lb pricing; everything else is skipped
so we only stage comparable, directly-usable prices.

Why not the official WF site? Prices on wholefoodsmarket.com require JavaScript
and an Amazon/WF store selection — not accessible without a headless browser.
"""
import re
import httpx
from bs4 import BeautifulSoup
from datetime import date

from .cut_matcher import match_cut, infer_price_unit

AD_URL = "https://www.iweeklyads.com/whole-foods-ad-specials/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Match: $3.99 lb Fresh Pork Sausages  OR  $8.99lb Dover Sole Fillets
_PRICE_RE = re.compile(
    r"\$\s*([\d.]+)\s*(?:\/?\s*lb\b)(.*?)(?=\$|\Z|;)",
    re.IGNORECASE,
)

# Match valid date in the paragraph header:  "valid May 13 – May 19, 2026"
_DATE_RE = re.compile(
    r"valid\s+\w+\s+\d+\s*[–\-]\s*(\w+)\s+(\d+),?\s*(\d{4})",
    re.IGNORECASE,
)

_MONTH_MAP = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
}

# Filter out non-meat items that match "lb" by accident
_SKIP_NAME_PATTERNS = [
    "mushroom", "avocado", "peppers", "salad", "bread", "cheese",
    "yogurt", "orange", "apple", "pear", "mango", "tomato", "berry",
    "strawberry", "raspberry", "cereal", "chip", "cracker", "coffee",
    "tea", "water", "juice", "broccoli", "asparagus", "kale",
    "spinach", "celery", "mango", "grapes", "lettuce", "arugula",
]


def _parse_sale_end(paragraph_text: str) -> str | None:
    m = _DATE_RE.search(paragraph_text)
    if not m:
        return None
    month_str, day, year = m.group(1).lower(), m.group(2), m.group(3)
    month_num = _MONTH_MAP.get(month_str)
    if not month_num:
        return None
    try:
        return f"{year}-{month_num}-{int(day):02d}"
    except ValueError:
        return None


def _is_current_week(paragraph_text: str) -> bool:
    """The aggregator labels the live ad with the current year."""
    return str(date.today().year) in paragraph_text and "valid" in paragraph_text.lower()


def _is_skip(name: str) -> bool:
    lower = name.lower()
    return any(skip in lower for skip in _SKIP_NAME_PATTERNS)


def _clean_name(raw: str) -> str:
    name = raw.strip().strip(";").strip()
    # Remove trailing punctuation/noise
    name = re.sub(r"[;,\.]+$", "", name).strip()
    # Truncate at next known noise words
    for cut_off in [" 2/", " 10/", " 5/", " 3/", " 4/$", " per lb", "(prime"]:
        idx = name.lower().find(cut_off)
        if idx > 2:
            name = name[:idx].strip()
    return name


async def fetch_wholefoods_deals() -> list[dict]:
    """
    Returns normalized staged deal candidates from the current Whole Foods weekly ad.
    Only items with explicit per-lb pricing are extracted.
    """
    results: list[dict] = []

    try:
        async with httpx.AsyncClient(
            timeout=15.0, follow_redirects=True, headers=HEADERS
        ) as client:
            resp = await client.get(AD_URL)
            if resp.status_code != 200:
                return results

            soup = BeautifulSoup(resp.text, "html.parser")

            # Find the current-week paragraph (contains "valid [Month Day–Day, Year]")
            current_para = None
            for p in soup.find_all("p"):
                text = p.get_text(" ", strip=True)
                if _is_current_week(text) and "$" in text:
                    current_para = text
                    break

            if not current_para:
                return results

            sale_end = _parse_sale_end(current_para)

            # Extract all "$X.XX lb Product Name" patterns
            seen = set()
            for m in _PRICE_RE.finditer(current_para):
                price_str = m.group(1)
                raw_name = _clean_name(m.group(2))

                if not raw_name or _is_skip(raw_name):
                    continue

                try:
                    price = float(price_str)
                except ValueError:
                    continue

                if price <= 0 or price > 200:
                    continue

                key = raw_name.lower()
                if key in seen:
                    continue
                seen.add(key)

                cut_name, confidence = match_cut(raw_name)
                results.append({
                    "source": "wholefoods",
                    "store_name": "Whole Foods Market",
                    "cut_name_raw": raw_name,
                    "cut_name_matched": cut_name,
                    "match_confidence": confidence,
                    "price": round(price, 2),
                    "price_unit": "per_lb",
                    "sale_end_date": sale_end,
                    "source_data": {
                        "url": AD_URL,
                        "note": "Whole Foods weekly ad — applies to both Memphis and Germantown stores",
                    },
                })

    except Exception:
        pass

    return results
