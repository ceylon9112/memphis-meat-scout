"""
Flipp / Wishabi weekly flyer scraper.

Uses the backflipp.wishabi.com API (no key required) to pull current weekly
ad items from Memphis-area grocery stores: Kroger, ALDI, Market Place,
Superlo Foods, Sprouts, Restaurant Depot, Gene Stimson Big Star.

Replaces the direct Walmart scraper (blocked by Cloudflare).
Walmart, if present in the flyer list, is included automatically.
"""
import httpx
from datetime import date

from .cut_matcher import match_cut, is_meat_product, infer_price_unit

WISHABI_BASE = "https://backflipp.wishabi.com/flipp"
DEFAULT_ZIP = "38103"  # Memphis, TN — used when no zip is specified

FOOD_MERCHANTS = {
    "kroger", "aldi", "market place", "superlo foods", "sprouts farmers market",
    "gene stimson big star", "restaurant depot", "walmart", "piggly wiggly",
    "food lion", "save a lot", "winn-dixie", "target", "costco", "sams club",
    "whole foods", "trader joe's", "publix", "food city", "h.g. hill",
    "natural grocers", "western supermarkets",
}

MEAT_KEYWORDS = [
    "beef", "pork", "chicken", "rib", "brisket", "steak", "roast",
    "chop", "wing", "shrimp", "salmon", "catfish", "turkey", "ground",
    "loin", "butt", "tenderloin", "sirloin", "chuck", "skirt", "tri-tip",
    "tri tip", "short rib", "brat", "sausage link", "rack of",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://flipp.com/",
}


def _is_food_merchant(merchant_name: str) -> bool:
    mn = merchant_name.lower().strip()
    return any(food in mn for food in FOOD_MERCHANTS)


def _is_meat_item(name: str, description: str = "") -> bool:
    text = (name + " " + (description or "")).lower()
    return any(kw in text for kw in MEAT_KEYWORDS)


def _parse_price(raw) -> float | None:
    if raw is None:
        return None
    try:
        val = float(str(raw).replace("$", "").replace(",", "").strip())
        return val if 0 < val < 500 else None
    except (ValueError, TypeError):
        return None


def _infer_sale_end(valid_to: str | None) -> str | None:
    if not valid_to:
        return None
    try:
        return valid_to[:10]
    except Exception:
        return None


async def fetch_flipp_deals(postal_code: str = DEFAULT_ZIP) -> list[dict]:
    """
    Returns normalized staged deal candidates from weekly flyers near ``postal_code``.
    Defaults to Memphis, TN (38103).  Pass any US zip to discover deals in other markets.
    """
    results: list[dict] = []
    seen: set[str] = set()
    today = date.today().isoformat()

    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True, headers=HEADERS) as client:
            # Step 1: get all flyers for the given zip
            resp = await client.get(
                f"{WISHABI_BASE}/flyers",
                params={"locale": "en-us", "postal_code": postal_code},
            )
            resp.raise_for_status()
            flyers = resp.json().get("flyers", [])

            # Step 2: filter to food merchants with current/upcoming flyers
            food_flyers = [
                f for f in flyers
                if _is_food_merchant(f.get("merchant", ""))
                and f.get("valid_to", today) >= today
            ]

            # Step 3: fetch items for each flyer
            for flyer in food_flyers:
                fid = flyer.get("id")
                merchant = flyer.get("merchant", "Unknown").strip()
                sale_end = _infer_sale_end(flyer.get("valid_to"))

                try:
                    item_resp = await client.get(f"{WISHABI_BASE}/flyers/{fid}")
                    if item_resp.status_code != 200:
                        continue
                    items = item_resp.json().get("items", [])
                except Exception:
                    continue

                for item in items:
                    name = (item.get("name") or item.get("short_name") or "").strip()
                    if not name or not _is_meat_item(name):
                        continue

                    price = _parse_price(item.get("price"))
                    if not price:
                        continue

                    key = f"flipp:{merchant.lower()}:{name.lower()}:{price}"
                    if key in seen:
                        continue
                    seen.add(key)

                    cut_name, confidence = match_cut(name)
                    price_unit = infer_price_unit(name)
                    item_sale_end = _infer_sale_end(item.get("valid_to")) or sale_end

                    results.append({
                        "source": "flipp",
                        "store_name": merchant,
                        "cut_name_raw": name,
                        "cut_name_matched": cut_name,
                        "match_confidence": confidence,
                        "price": round(price, 2),
                        "price_unit": price_unit,
                        "sale_end_date": item_sale_end,
                        "source_data": {
                            "flyer_id": fid,
                            "item_id": item.get("id"),
                            "brand": item.get("brand"),
                            "valid_from": item.get("valid_from", "")[:10],
                            "valid_to": item_sale_end,
                        },
                    })

    except Exception:
        pass

    return results
