"""
Kroger Developer API client — real-time product prices.

Uses OAuth2 client credentials flow. Credentials are read from environment
variables (set as Azure Container App secrets):

  KROGER_CLIENT_ID       — developer.kroger.com Client ID
  KROGER_CLIENT_SECRET   — developer.kroger.com Client Secret
  KROGER_LOCATION_ID     — specific store location ID (e.g. 02500419)

Docs: https://developer.kroger.com/api-products/api/products-api
"""
import os
import base64
import httpx
from datetime import datetime, timedelta
from typing import Optional

from .cut_matcher import match_cut, is_meat_product, infer_price_unit

KROGER_BASE = "https://api.kroger.com/v1"

# All canonical meat categories we want to pull prices for
SEARCH_TERMS = [
    # Beef
    "beef brisket", "chuck roast", "beef short ribs", "ribeye steak",
    "sirloin steak", "new york strip steak", "t-bone steak", "filet mignon",
    "skirt steak", "tri tip", "ground beef 80", "ground beef 90",
    "ground chuck", "lean ground beef",
    # Pork
    "baby back ribs", "spare ribs", "st louis ribs", "boston butt",
    "pork shoulder", "pork tenderloin", "bone-in pork chops",
    "boneless pork chops", "pork loin", "slab bacon", "hot dogs",
    "smoked sausage", "bratwurst",
    # Poultry
    "whole chicken", "boneless chicken breast", "chicken thighs",
    "chicken wings", "chicken leg quarters", "whole turkey",
    "turkey breast", "ground turkey",
    # Seafood
    "catfish", "gulf shrimp", "salmon fillet", "tuna steak",
]

_token: Optional[str] = None
_token_expires: Optional[datetime] = None


def _is_configured() -> bool:
    return bool(os.getenv("KROGER_CLIENT_ID") and os.getenv("KROGER_CLIENT_SECRET"))


def _get_location_id() -> str:
    """Return the configured store location ID, falling back to empty string."""
    return os.getenv("KROGER_LOCATION_ID", "").strip()


async def _get_token(client: httpx.AsyncClient) -> Optional[str]:
    global _token, _token_expires
    if _token and _token_expires and datetime.utcnow() < _token_expires:
        return _token

    client_id     = os.getenv("KROGER_CLIENT_ID", "")
    client_secret = os.getenv("KROGER_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        return None

    creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    resp = await client.post(
        f"{KROGER_BASE}/connect/oauth2/token",
        headers={
            "Authorization": f"Basic {creds}",
            "Content-Type":  "application/x-www-form-urlencoded",
        },
        data={"grant_type": "client_credentials", "scope": "product.compact"},
    )
    if resp.status_code != 200:
        return None

    data = resp.json()
    _token = data.get("access_token")
    _token_expires = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 1800) - 60)
    return _token


async def _resolve_location_id(client: httpx.AsyncClient, token: str) -> Optional[str]:
    """Use the env-supplied location ID if available; otherwise discover via zip."""
    loc_id = _get_location_id()
    if loc_id:
        return loc_id

    # Fallback: discover nearest store to Memphis zip
    resp = await client.get(
        f"{KROGER_BASE}/locations",
        headers={"Authorization": f"Bearer {token}"},
        params={"filter.zipCode": "38103", "filter.radiusMiles": 25, "filter.limit": 1},
    )
    if resp.status_code == 200:
        locations = resp.json().get("data", [])
        if locations:
            return locations[0]["locationId"]
    return None


async def fetch_kroger_deals() -> list[dict]:
    """
    Returns normalized deal candidates from the Kroger Products API.
    Returns [] if credentials are not configured or the API is unavailable.
    Prefers promotional (sale) prices over regular prices.
    """
    if not _is_configured():
        return []

    results: list[dict] = []
    seen:    set[str]   = set()

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            token = await _get_token(client)
            if not token:
                return []

            location_id = await _resolve_location_id(client, token)
            if not location_id:
                return []

            for term in SEARCH_TERMS:
                try:
                    resp = await client.get(
                        f"{KROGER_BASE}/products",
                        headers={"Authorization": f"Bearer {token}"},
                        params={
                            "filter.term":       term,
                            "filter.locationId": location_id,
                            "filter.limit":      50,
                        },
                    )
                    if resp.status_code != 200:
                        continue

                    for product in resp.json().get("data", []):
                        desc = (product.get("description") or "").strip()
                        if not desc or not is_meat_product(desc):
                            continue

                        for item in product.get("items", []):
                            price_data = item.get("price") or {}
                            # Prefer promotional (sale) price; fall back to regular
                            price = price_data.get("promo") or price_data.get("regular")
                            if not price or float(price) <= 0:
                                continue

                            is_promo = bool(price_data.get("promo"))
                            key = f"kroger:{location_id}:{desc.lower()}:{price}"
                            if key in seen:
                                continue
                            seen.add(key)

                            sold_by    = item.get("soldBy", "")
                            cut_name, confidence = match_cut(desc)
                            price_unit = infer_price_unit(desc, sold_by)

                            results.append({
                                "source":             "kroger",
                                "store_name":         "Kroger",
                                "cut_name_raw":       desc,
                                "cut_name_matched":   cut_name,
                                "match_confidence":   confidence,
                                "price":              round(float(price), 2),
                                "price_unit":         price_unit,
                                "source_zip":         "38103",
                                "source_data": {
                                    "product_id":  product.get("productId"),
                                    "location_id": location_id,
                                    "sold_by":     sold_by,
                                    "size":        item.get("size"),
                                    "is_promo":    is_promo,
                                    "regular_price": price_data.get("regular"),
                                },
                            })
                except Exception:
                    continue

    except Exception:
        pass

    return results
