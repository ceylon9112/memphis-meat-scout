"""
Scraper for Ramon's Meat Market (ramonsmeatmarket.com).

Ramon's is a local Memphis butcher at 1616 Getwell Rd. They publish their
current prices on a Wix storefront. We scrape two pages:
  - /individual-meats  — per-cut pricing (ribeye, T-bone, ground beef, etc.)
  - /meat-bundles      — bundle packages (Cook Out Special, Freezer Filler, etc.)

The Wix HTML embeds plain text in the form:
    "Quick View [Product Name] Price $X.XX [qualifier] Excluding Sales Tax"

No API key required. Page renders fully server-side (no JS needed for prices).
"""
import re
import httpx
from bs4 import BeautifulSoup

from .cut_matcher import match_cut, infer_price_unit

RAMONS_BASE = "https://www.ramonsmeatmarket.com"

PAGES = [
    ("/individual-meats", "individual"),
    # Bundles are excluded — they are multi-cut packages, not per-cut prices.
    # ("/meat-bundles", "bundle"),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Extract: "Quick View [NAME] Price $PRICE [per X Pound|Out of Stock|...]"
_PRODUCT_RE = re.compile(
    r"Quick View\s+(.+?)\s+Price\s+\$([\d,]+\.?\d*)"
    r"(?:\s*\$[\d,]+\.?\d*\s*per\s+([\d.]+)\s+Pounds?)?"
    r"(?:\s*(?:Out of Stock|Excluding Sales Tax|Add to Cart))?",
    re.IGNORECASE,
)

# Items to skip (non-meat noise, promotional text, etc.)
_SKIP_PATTERNS = [
    "kebab special",  # per-package bundles — no per-lb price to compare
    "shish kebab",
]


def _clean_name(raw: str) -> str:
    raw = raw.strip()
    # Remove "New " prefix Wix sometimes adds for recently updated items
    raw = re.sub(r"^New\s+", "", raw)
    return raw


def _parse_price_unit(name: str, per_pounds_str: str | None) -> str:
    """
    Ramon's prices are almost always 'per unit' (per steak / per pack).
    If Wix shows a 'per X Pound' qualifier, treat as per_lb.
    """
    if per_pounds_str:
        return "per_lb"
    lower = name.lower()
    if any(w in lower for w in ["ground beef", "ground turkey", "ground"]):
        return "per_lb"
    return "per_unit"


def _extract_products(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    products = []
    seen = set()

    for m in _PRODUCT_RE.finditer(text):
        raw_name = _clean_name(m.group(1))
        price_str = m.group(2).replace(",", "")
        per_pounds = m.group(3)  # e.g. "1" if "per 1 Pound"

        if any(skip in raw_name.lower() for skip in _SKIP_PATTERNS):
            continue

        try:
            price = float(price_str)
        except ValueError:
            continue

        if price <= 0 or price > 999:
            continue

        # If per_pounds is provided, recalculate per-lb price
        if per_pounds:
            try:
                lbs = float(per_pounds)
                price = round(price / lbs, 2) if lbs > 1 else price
            except ValueError:
                pass

        key = f"{raw_name.lower()}:{price}"
        if key in seen:
            continue
        seen.add(key)

        products.append({
            "name": raw_name,
            "price": round(price, 2),
            "price_unit": _parse_price_unit(raw_name, per_pounds),
        })

    return products


async def fetch_ramons_deals() -> list[dict]:
    """
    Returns normalized staged deal candidates from Ramon's Meat Market.
    """
    results: list[dict] = []

    async with httpx.AsyncClient(
        timeout=15.0, follow_redirects=True, headers=HEADERS
    ) as client:
        for path, page_type in PAGES:
            try:
                resp = await client.get(f"{RAMONS_BASE}{path}")
                if resp.status_code != 200:
                    continue

                products = _extract_products(resp.text)

                for product in products:
                    name = product["name"]
                    price = product["price"]
                    price_unit = product["price_unit"]

                    cut_name, confidence = match_cut(name)
                    # Override infer_price_unit with what we detected from the page
                    results.append({
                        "source": "ramons",
                        "store_name": "Ramon's Meat Market",
                        "cut_name_raw": name,
                        "cut_name_matched": cut_name,
                        "match_confidence": confidence,
                        "price": price,
                        "price_unit": price_unit,
                        "sale_end_date": None,  # Ramon's prices are standing prices
                        "source_data": {
                            "page": page_type,
                            "url": f"{RAMONS_BASE}{path}",
                        },
                    })

            except Exception:
                continue

    return results
