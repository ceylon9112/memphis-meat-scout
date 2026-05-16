"""
Trader Joe's product catalog scraper via their GraphQL API.

TJ's doesn't publish weekly sale ads — their prices are consistent year-round
(Every Day Low Prices model). This service pulls current meat/seafood/poultry
prices from their public GraphQL endpoint, which is the same data powering
traderjoes.com.

The Germantown, TN store (38138) sells from the national TJ catalog at
national prices. No store-specific pricing differences exist.

No API key required.
"""
import asyncio
import httpx

from .cut_matcher import match_cut, infer_price_unit

GRAPHQL_URL = "https://www.traderjoes.com/api/graphql"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Referer": "https://www.traderjoes.com/",
    "Origin": "https://www.traderjoes.com",
}

SEARCH_QUERY = """
query SearchProducts($search: String!, $pageSize: Int, $currentPage: Int) {
  products(
    search: $search
    filter: { published: { eq: "1" } }
    pageSize: $pageSize
    currentPage: $currentPage
  ) {
    items {
      sku
      name
      item_title
      sales_size
      sales_uom_description
      retail_price
      price_range {
        minimum_price { final_price { value } }
      }
    }
    total_count
    page_info { total_pages }
  }
}
"""

MEAT_SEARCH_TERMS = [
    # Fewer broad terms → fewer requests → less rate-limit exposure.
    # TJ's search is full-text; these cover almost the full meat catalog.
    "beef",
    "pork",
    "chicken breast thigh wing",
    "turkey ground",
    "salmon shrimp",
    "tuna catfish lamb",
]

# Skip items that are clearly prepared foods, dog treats, condiments, etc.
_SKIP_TERMS = [
    "dog treat", "dog food", "pet ", "for pets",
    "soup", "salad", "sandwich", "wrap", "bowl", "burrito", "quesadilla",
    "enchilada", "lasagna", "pizza", "pasta", "ravioli", "nugget",
    "meatball", "meatloaf", "sausage", "hot dog", "frank",
    "broth", "gravy", "sauce", "dip", "spread", "salsa", "seasoning",
    "rub", "spice", "coffee", "cookie", "snack", "chips", "fried rice",
    "stir fry", "lo mein", "noodle", "dumpling", "bao", "taco", "burge",
    "patties",  # frozen convenience patties — too processed
    "smoked pulled", "bbq", "pulled chicken", "pulled pork",
    "corned beef",  # too niche
    "holiday", "hol ",
    "organic whole turkey",  # holiday seasonal, no regular price
    "summer sausage", "bresaola", "prosciutto",
    "meatless", "plant based", "veggie", "turkeyless",
]

# Require at least one of these to confirm it's raw/fresh meat
_REQUIRE_FRESH = [
    "steak", "fillet", "filet", "loin", "chop", "roast", "ribs",
    "breast", "thigh", "wing", "quarter", "ground", "shrimp",
    "brisket", "chuck", "skirt", "ribeye", "sirloin", "strip",
    "shoulder", "butt", "tenderloin", "salmon", "catfish", "tuna",
    "whole chicken", "whole turkey", "leg quarter",
]


def _is_raw_meat(name: str, uom: str) -> bool:
    lower = name.lower()
    # Skip prepared/processed foods
    if any(skip in lower for skip in _SKIP_TERMS):
        return False
    # Must be sold by weight (per_lb) or be a fresh cut
    is_per_lb = uom and ("lb" in uom.lower() or "oz" in uom.lower())
    has_fresh_kw = any(kw in lower for kw in _REQUIRE_FRESH)
    return is_per_lb and has_fresh_kw


def _extract_price(item: dict) -> float | None:
    # retail_price is the displayed price string or number
    raw = item.get("retail_price")
    if raw is not None:
        try:
            return float(str(raw).replace("$", "").strip())
        except (ValueError, TypeError):
            pass
    # fallback: price_range
    try:
        return float(
            item["price_range"]["minimum_price"]["final_price"]["value"]
        )
    except (KeyError, TypeError, ValueError):
        return None


def _parse_price_per_lb(price: float, size: str, uom: str) -> tuple[float, str]:
    """
    TJ's prices are per-unit (per package).
    If the item is sold as "1 Lb" we can use the price as per_lb.
    For other sizes (e.g. 20 Oz) we convert to per_lb.
    """
    if not size or not uom:
        return price, "per_unit"

    uom_lower = uom.lower()
    try:
        qty = float(size.replace(",", "").strip())
    except ValueError:
        return price, "per_unit"

    if "lb" in uom_lower:
        if qty == 1.0:
            return round(price, 2), "per_lb"
        else:
            return round(price / qty, 2), "per_lb"
    elif "oz" in uom_lower:
        lbs = qty / 16.0
        if lbs > 0:
            return round(price / lbs, 2), "per_lb"

    return price, "per_unit"


async def fetch_traderjoes_deals() -> list[dict]:
    """
    Returns normalized staged deal candidates from Trader Joe's national catalog.
    These are everyday prices (not weekly specials) from the Germantown TN store.
    Requests are rate-limited to avoid Akamai CDN blocks.
    """
    seen_skus: set[str] = set()
    results: list[dict] = []
    semaphore = asyncio.Semaphore(2)  # max 2 concurrent requests

    async def fetch_one(client: httpx.AsyncClient, term: str):
        async with semaphore:
            await asyncio.sleep(0.5)  # gentle pacing
            return await client.post(GRAPHQL_URL, json={
                "query": SEARCH_QUERY,
                "variables": {"search": term, "pageSize": 50, "currentPage": 1}
            })

    async with httpx.AsyncClient(timeout=20.0, headers=HEADERS) as client:
        tasks = [fetch_one(client, term) for term in MEAT_SEARCH_TERMS]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for resp in responses:
            if isinstance(resp, Exception):
                continue
            if resp.status_code != 200:
                continue
            try:
                data = resp.json()
            except Exception:
                continue

            items = (
                (data.get("data") or {})
                .get("products") or {}
            ).get("items") or []

            for item in items:
                sku = item.get("sku", "")
                if not sku or sku in seen_skus:
                    continue

                name = (item.get("item_title") or item.get("name") or "").strip()
                if not name:
                    continue

                sales_size = str(item.get("sales_size") or "").strip()
                uom = str(item.get("sales_uom_description") or "").strip()

                if not _is_raw_meat(name, uom):
                    continue

                price_raw = _extract_price(item)
                if not price_raw or price_raw <= 0:
                    continue

                price, price_unit = _parse_price_per_lb(price_raw, sales_size, uom)

                seen_skus.add(sku)
                cut_name, confidence = match_cut(name)

                results.append({
                    "source": "traderjoes",
                    "store_name": "Trader Joe's",
                    "cut_name_raw": name,
                    "cut_name_matched": cut_name,
                    "match_confidence": confidence,
                    "price": price,
                    "price_unit": price_unit,
                    "sale_end_date": None,
                    "source_data": {
                        "sku": sku,
                        "sales_size": sales_size,
                        "uom": uom,
                        "original_price": price_raw,
                        "note": "Everyday price — TJ's does not run weekly sales",
                    },
                })

    return results
