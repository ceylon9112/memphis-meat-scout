"""
Walmart product search scraper.

Parses the __NEXT_DATA__ JSON embedded in Walmart.com search pages.
No API key required. Targets Walmart.com product search for each cut.
Note: scraping is against Walmart's ToS — use for internal/proof-of-concept only.
"""
import json
import re
import httpx
from bs4 import BeautifulSoup
from typing import Optional

from .cut_matcher import match_cut, is_meat_product, infer_price_unit

WALMART_SEARCH = "https://www.walmart.com/search"
MEMPHIS_ZIP = "38103"

SEARCH_TERMS = [
    "beef brisket", "chuck roast", "beef short ribs", "ribeye steak",
    "skirt steak", "ground beef", "baby back ribs", "spare ribs pork",
    "boston butt pork shoulder", "pork tenderloin", "bone-in pork chops",
    "whole chicken", "chicken thighs bone-in", "chicken wings fresh",
    "chicken leg quarters", "whole turkey", "catfish fillet", "shrimp fresh",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
}


def _extract_next_data(html: str) -> Optional[dict]:
    try:
        soup = BeautifulSoup(html, "lxml")
        tag = soup.find("script", {"id": "__NEXT_DATA__"})
        if tag and tag.string:
            return json.loads(tag.string)
    except Exception:
        pass
    return None


def _parse_price_string(price_str: str) -> Optional[float]:
    """Extract numeric price from strings like '$4.98', '4.98/lb', '$12.97 /lb'."""
    if not price_str:
        return None
    m = re.search(r"\$?([\d]+\.[\d]{1,2})", str(price_str))
    return float(m.group(1)) if m else None


def _extract_items(data: dict) -> list[dict]:
    """Navigate the __NEXT_DATA__ JSON to find search result items."""
    raw_items = []
    try:
        # Primary path (current Walmart Next.js structure)
        stacks = (
            data["props"]["pageProps"]["initialData"]["searchResult"]["itemStacks"]
        )
        for stack in stacks:
            raw_items.extend(stack.get("items", []))
    except (KeyError, TypeError):
        pass

    if not raw_items:
        # Fallback: brute-force search for a list of dicts with "name" and "price"
        text = json.dumps(data)
        try:
            matches = re.findall(r'"name"\s*:\s*"([^"]+)".*?"price"\s*:\s*([\d.]+)', text)
            for name, price in matches[:30]:
                raw_items.append({"name": name, "price": float(price)})
        except Exception:
            pass

    return raw_items


async def fetch_walmart_deals() -> list[dict]:
    """
    Returns list of normalized staged deal candidates from Walmart.
    Returns [] if scraping fails.
    """
    results = []
    seen: set[str] = set()

    try:
        async with httpx.AsyncClient(
            timeout=20.0,
            headers=HEADERS,
            follow_redirects=True,
        ) as client:
            for term in SEARCH_TERMS:
                try:
                    resp = await client.get(
                        WALMART_SEARCH,
                        params={"q": term, "affinityOverride": "default"},
                    )
                    if resp.status_code != 200:
                        continue

                    data = _extract_next_data(resp.text)
                    if not data:
                        continue

                    items = _extract_items(data)
                    for item in items:
                        name = item.get("name") or item.get("description") or ""
                        if not name or not is_meat_product(name):
                            continue

                        # Price: try several possible paths
                        price = None
                        price_info = item.get("priceInfo") or {}
                        for path in [
                            item.get("price"),
                            price_info.get("linePrice"),
                            price_info.get("unitPrice"),
                            price_info.get("currentPrice"),
                        ]:
                            price = _parse_price_string(str(path)) if path else None
                            if price:
                                break

                        if not price or price <= 0:
                            continue

                        key = f"walmart:{name.lower()}:{price}"
                        if key in seen:
                            continue
                        seen.add(key)

                        unit_hint = str(price_info.get("unitPriceDisplayCondition", ""))
                        sold_by = "WEIGHT" if "/lb" in unit_hint else item.get("salesUnit", "")
                        cut_name, confidence = match_cut(name)
                        price_unit = infer_price_unit(name, sold_by)

                        results.append({
                            "source": "walmart",
                            "store_name": "Walmart",
                            "cut_name_raw": name,
                            "cut_name_matched": cut_name,
                            "match_confidence": confidence,
                            "price": round(float(price), 2),
                            "price_unit": price_unit,
                            "source_data": {
                                "unit_price_display": unit_hint,
                                "sales_unit": sold_by,
                                "item_id": item.get("usItemId") or item.get("itemId"),
                            },
                        })

                except Exception:
                    continue

    except Exception:
        pass

    return results
