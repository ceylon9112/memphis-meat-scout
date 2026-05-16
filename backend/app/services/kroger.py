"""
Kroger Developer API client.

Free account + client credentials required:
  https://developer.kroger.com → Create App → copy Client ID and Secret
  Add to backend/.env:
    KROGER_CLIENT_ID=your_client_id
    KROGER_CLIENT_SECRET=your_client_secret

Docs: https://developer.kroger.com/api-products/api/products-api
"""
import os
import base64
import httpx
from datetime import datetime, timedelta
from typing import Optional

from .cut_matcher import match_cut, is_meat_product, infer_price_unit

KROGER_BASE = "https://api.kroger.com/v1"
MEMPHIS_ZIP = "38103"
SEARCH_RADIUS_MILES = 35

# Search terms targeted at our cut list
SEARCH_TERMS = [
    "beef brisket", "chuck roast", "short ribs", "ribeye steak",
    "skirt steak", "tri tip", "ground beef",
    "baby back ribs", "spare ribs", "pork shoulder", "boston butt",
    "pork tenderloin", "pork chops", "pork loin", "slab bacon",
    "whole chicken", "chicken thighs", "chicken wings", "leg quarters",
    "whole turkey", "turkey breast",
    "catfish", "shrimp", "salmon",
]

_token: Optional[str] = None
_token_expires: Optional[datetime] = None
_location_ids: list[str] = []


def _is_configured() -> bool:
    return bool(os.getenv("KROGER_CLIENT_ID") and os.getenv("KROGER_CLIENT_SECRET"))


async def _get_token(client: httpx.AsyncClient) -> Optional[str]:
    global _token, _token_expires
    if _token and _token_expires and datetime.utcnow() < _token_expires:
        return _token

    client_id = os.getenv("KROGER_CLIENT_ID", "")
    client_secret = os.getenv("KROGER_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        return None

    creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    resp = await client.post(
        f"{KROGER_BASE}/connect/oauth2/token",
        headers={"Authorization": f"Basic {creds}", "Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "client_credentials", "scope": "product.compact"},
    )
    if resp.status_code != 200:
        return None

    data = resp.json()
    _token = data.get("access_token")
    expires_in = data.get("expires_in", 1800)
    _token_expires = datetime.utcnow() + timedelta(seconds=expires_in - 60)
    return _token


async def _get_memphis_location_ids(client: httpx.AsyncClient, token: str) -> list[str]:
    global _location_ids
    if _location_ids:
        return _location_ids

    resp = await client.get(
        f"{KROGER_BASE}/locations",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "filter.zipCode": MEMPHIS_ZIP,
            "filter.radiusMiles": SEARCH_RADIUS_MILES,
            "filter.limit": 10,
        },
    )
    if resp.status_code != 200:
        return []

    locations = resp.json().get("data", [])
    _location_ids = [loc["locationId"] for loc in locations]
    return _location_ids


async def fetch_kroger_deals() -> list[dict]:
    """
    Returns list of normalized staged deal candidates from Kroger.
    Returns [] if not configured or API unavailable.
    """
    if not _is_configured():
        return []

    results = []
    seen: set[str] = set()

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            token = await _get_token(client)
            if not token:
                return []

            location_ids = await _get_memphis_location_ids(client, token)
            if not location_ids:
                return []

            # Use first location for pricing (prices are similar across metro)
            location_id = location_ids[0]

            for term in SEARCH_TERMS:
                try:
                    resp = await client.get(
                        f"{KROGER_BASE}/products",
                        headers={"Authorization": f"Bearer {token}"},
                        params={
                            "filter.term": term,
                            "filter.locationId": location_id,
                            "filter.limit": 50,
                        },
                    )
                    if resp.status_code != 200:
                        continue

                    for product in resp.json().get("data", []):
                        desc = product.get("description", "")
                        if not desc or not is_meat_product(desc):
                            continue

                        for item in product.get("items", []):
                            price_data = item.get("price", {})
                            price = price_data.get("promo") or price_data.get("regular")
                            if not price:
                                continue

                            key = f"kroger:{desc.lower()}:{price}"
                            if key in seen:
                                continue
                            seen.add(key)

                            sold_by = item.get("soldBy", "")
                            cut_name, confidence = match_cut(desc)
                            price_unit = infer_price_unit(desc, sold_by)

                            results.append({
                                "source": "kroger",
                                "store_name": "Kroger",
                                "cut_name_raw": desc,
                                "cut_name_matched": cut_name,
                                "match_confidence": confidence,
                                "price": round(float(price), 2),
                                "price_unit": price_unit,
                                "source_data": {
                                    "product_id": product.get("productId"),
                                    "location_id": location_id,
                                    "sold_by": sold_by,
                                    "size": item.get("size"),
                                },
                            })
                except Exception:
                    continue

    except Exception:
        pass

    return results
