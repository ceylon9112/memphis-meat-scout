from bson import ObjectId
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
from typing import Optional
import httpx

# ─── Geo helpers ──────────────────────────────────────────────────────────────

_zip_cache: dict[str, tuple[float, float]] = {}


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Return distance in miles between two lat/lng points."""
    R = 3958.8
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


async def zip_to_coords(zip_code: str) -> tuple[Optional[float], Optional[float]]:
    """Convert a US zip code to (lat, lng) using the free zippopotam.us API."""
    zip_code = zip_code.strip()
    if zip_code in _zip_cache:
        return _zip_cache[zip_code]
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"https://api.zippopotam.us/us/{zip_code}")
            if resp.status_code == 200:
                place = resp.json()["places"][0]
                coords = float(place["latitude"]), float(place["longitude"])
                _zip_cache[zip_code] = coords
                return coords
    except Exception:
        pass
    return None, None


# ─── Document serialisers ─────────────────────────────────────────────────────

def doc_to_vendor(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "city": doc["city"],
        "state": doc["state"],
        "type": doc["type"],
        "active": doc["active"],
        "featured": doc.get("featured", False),
        "lat": doc.get("lat"),
        "lng": doc.get("lng"),
        "zip_code": doc.get("zip_code"),
        "address": doc.get("address"),
        "distance_miles": doc.get("_distance"),
        "created_at": doc["created_at"],
    }


def doc_to_cut(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "category": doc["category"],
        "active": doc["active"],
        "created_at": doc["created_at"],
    }


def doc_to_deal(doc: dict, vendor_map: dict, cut_map: dict) -> dict:
    vid = str(doc.get("vendor_id", ""))
    cid = str(doc.get("cut_id", ""))
    vendor = vendor_map.get(vid, {})
    cut = cut_map.get(cid, {})
    return {
        "id": str(doc["_id"]),
        "vendor_id": vid,
        "cut_id": cid,
        "vendor_name": vendor.get("name", "Unknown"),
        "cut_name": cut.get("name", "Unknown"),
        "category": cut.get("category", ""),
        "price": round(float(doc.get("price", 0)), 2),
        "price_unit": doc.get("price_unit"),
        "verified_date": doc.get("verified_date"),
        "sale_end_date": doc.get("sale_end_date"),
        "notes": doc.get("notes"),
        "active": doc.get("active", True),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


async def fetch_deals_with_join(db, query: dict) -> list:
    deals = await db.deals.find(query).to_list(2000)
    if not deals:
        return []

    vendor_oids = list({d["vendor_id"] for d in deals if "vendor_id" in d})
    cut_oids = list({d["cut_id"] for d in deals if "cut_id" in d})

    vendors = await db.vendors.find({"_id": {"$in": vendor_oids}}).to_list(500)
    cuts = await db.meat_cuts.find({"_id": {"$in": cut_oids}}).to_list(500)

    vendor_map = {str(v["_id"]): v for v in vendors}
    cut_map = {str(c["_id"]): c for c in cuts}

    return [doc_to_deal(d, vendor_map, cut_map) for d in deals]
