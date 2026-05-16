from fastapi import APIRouter, Query
from typing import Optional
from ..database import get_db
from ..utils import doc_to_vendor, zip_to_coords, haversine

router = APIRouter()


@router.get("/vendors")
async def list_vendors(
    zip: Optional[str] = Query(None, description="US zip code for proximity search"),
    radius: float = Query(50, description="Search radius in miles"),
):
    db = get_db()
    vendors = await db.vendors.find({"active": True}).to_list(1000)

    if zip:
        user_lat, user_lng = await zip_to_coords(zip)
        if user_lat is not None and user_lng is not None:
            geo_vendors = []
            for v in vendors:
                if v.get("lat") is not None and v.get("lng") is not None:
                    dist = haversine(user_lat, user_lng, v["lat"], v["lng"])
                    if dist <= radius:
                        v["_distance"] = round(dist, 1)
                        geo_vendors.append(v)
            geo_vendors.sort(key=lambda v: (not v.get("featured", False), v.get("_distance", 9999)))
            return [doc_to_vendor(v) for v in geo_vendors]

    vendors.sort(key=lambda v: (not v.get("featured", False), v.get("name", "").lower()))
    return [doc_to_vendor(v) for v in vendors]
