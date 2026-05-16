"""
The Fresh Market weekly specials scraper.

Source: thefreshmarket.com homepage __NEXT_DATA__ JSON blob, which contains
the current weekly specials board with exact prices, departments, and sale dates.

Coverage: all items TFM features in their weekly "specials board" for Tennessee
stores (boards that include store #39 Germantown, #41 Memphis S White Station,
and #194 Memphis Union Ave).  Typically 3–8 meat/seafood items per week.

Why this works without Selenium: The homepage is server-side rendered (Next.js
getStaticProps) and embeds the full specials JSON inline in __NEXT_DATA__ — no
JavaScript execution or login required.
"""
import re
import json
import httpx

from .cut_matcher import match_cut, infer_price_unit

HOME_URL = "https://www.thefreshmarket.com/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# TFM store numbers for the Memphis / Germantown area
TN_STORE_NUMBERS = {
    39,   # Poplar Ave, Germantown 38138
    41,   # S White Station Rd, Memphis 38117
    194,  # Union Ave, Memphis 38104
}

# Departments we care about (Poultry and Pork are rare but included for future items)
MEAT_DEPARTMENTS = {"Meat", "Seafood", "Poultry", "Pork"}

# Price string patterns
# "$6.49 lb"   "$13.99 ea"   "$8.99 lb"   "2/$7"
_PRICE_RE = re.compile(
    r"^\$?([\d.]+)\s*(?:\/\s*lb|lb|per lb)?\s*$|"
    r"^(\d+)/\$([\d.]+)$|"
    r"^\$([\d.]+)\s+ea",
    re.IGNORECASE,
)


def _parse_price(price_str: str | None) -> tuple[float | None, str]:
    """Returns (price, unit) from a raw price string like '$6.49 lb' or '$13.99 ea'."""
    if not price_str:
        return None, "per_lb"

    s = price_str.strip()

    # "$X.XX lb"
    m = re.match(r"^\$?([\d.]+)\s*(?:\/?\s*lb|per\s*lb)", s, re.IGNORECASE)
    if m:
        return float(m.group(1)), "per_lb"

    # "$X.XX ea"
    m = re.match(r"^\$?([\d.]+)\s*ea", s, re.IGNORECASE)
    if m:
        return float(m.group(1)), "per_unit"

    # "N/$X.XX" (multi-buy)
    m = re.match(r"^(\d+)/\$?([\d.]+)$", s)
    if m:
        count, total = int(m.group(1)), float(m.group(2))
        return round(total / count, 2), "per_unit"

    # Plain dollar amount
    m = re.match(r"^\$?([\d.]+)$", s)
    if m:
        return float(m.group(1)), "per_unit"

    return None, "per_lb"


def _boards_for_tn(specials: dict) -> list[dict]:
    """Return all specials boards that include at least one TN (Memphis/Germantown) store."""
    result = []
    for board in specials.values():
        stores = board.get("applicableStoresCollection", {}).get("items", [])
        nums = {s.get("storeNumber") for s in stores}
        if nums & TN_STORE_NUMBERS:
            result.append(board)
    return result


async def fetch_freshmarket_deals() -> list[dict]:
    """
    Returns normalized staged deal candidates from the current
    Fresh Market weekly specials for the Memphis / Germantown stores.
    """
    results: list[dict] = []

    try:
        async with httpx.AsyncClient(
            timeout=20.0, follow_redirects=True, headers=HEADERS
        ) as client:
            resp = await client.get(HOME_URL)
            if resp.status_code != 200:
                return results

            # Extract embedded __NEXT_DATA__ JSON
            m = re.search(
                r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
                resp.text,
                re.DOTALL,
            )
            if not m:
                return results

            data = json.loads(m.group(1))
            specials = (
                data.get("props", {})
                .get("pageProps", {})
                .get("weeklySpecialsContent", {})
            )

            tn_boards = _boards_for_tn(specials)
            seen: set[str] = set()

            for board in tn_boards:
                sale_end = board.get("endDate", "")[:10] or None
                items = board.get("specialItemsCollection", {}).get("items", [])

                for item in items:
                    product = item.get("product") or {}
                    dept = product.get("department", "")
                    if dept not in MEAT_DEPARTMENTS:
                        continue

                    name = item.get("specialItemName") or product.get("name") or ""
                    name = name.strip()
                    if not name or name.upper().startswith("BROWSE"):
                        continue

                    price_raw = item.get("specialMarketingPrice") or ""
                    price, unit = _parse_price(price_raw)
                    if price is None or price <= 0:
                        continue

                    # Size/description
                    desc = (
                        product.get("shortDescriptionForSpecials")
                        or product.get("description")
                        or ""
                    ).strip()

                    dedup_key = name.lower()
                    if dedup_key in seen:
                        continue
                    seen.add(dedup_key)

                    cut_name, confidence = match_cut(name)
                    results.append({
                        "source": "freshmarket",
                        "store_name": "The Fresh Market",
                        "cut_name_raw": name,
                        "cut_name_matched": cut_name,
                        "match_confidence": confidence,
                        "price": round(price, 2),
                        "price_unit": unit,
                        "sale_end_date": sale_end,
                        "source_data": {
                            "url": HOME_URL,
                            "department": dept,
                            "description": desc,
                            "savings": item.get("specialMarketingSavings", ""),
                            "note": (
                                "Applies to Germantown (Poplar Ave), "
                                "Memphis (S White Station Rd), and Memphis (Union Ave) stores"
                            ),
                        },
                    })

    except Exception:
        pass

    return results
