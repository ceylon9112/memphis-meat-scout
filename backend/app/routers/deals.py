from fastapi import APIRouter, Query, HTTPException, Request
from typing import Optional
from datetime import date, timedelta
from ..database import get_db
from ..utils import fetch_deals_with_join, zip_to_coords, haversine

router = APIRouter()


def active_cutoff() -> str:
    return (date.today() - timedelta(days=6)).isoformat()


@router.get("/deals")
async def list_deals(
    category: Optional[str] = Query(None),
    vendor_id: Optional[str] = Query(None),
    cut_id: Optional[str] = Query(None),
    sort: Optional[str] = Query("recent"),
    zip: Optional[str] = Query(None, description="US zip code for proximity filter"),
    radius: float = Query(50, description="Search radius in miles"),
):
    from bson import ObjectId

    db = get_db()
    query: dict = {"active": True, "verified_date": {"$gte": active_cutoff()}}

    if vendor_id:
        try:
            query["vendor_id"] = ObjectId(vendor_id)
        except Exception:
            return []
    if cut_id:
        try:
            query["cut_id"] = ObjectId(cut_id)
        except Exception:
            return []

    # If a zip is supplied, restrict to vendors within the radius first
    if zip and not vendor_id:
        user_lat, user_lng = await zip_to_coords(zip)
        if user_lat is not None and user_lng is not None:
            nearby = await db.vendors.find(
                {"active": True, "lat": {"$ne": None}, "lng": {"$ne": None}}
            ).to_list(1000)
            nearby_ids = [
                v["_id"] for v in nearby
                if haversine(user_lat, user_lng, v["lat"], v["lng"]) <= radius
            ]
            if nearby_ids:
                query["vendor_id"] = {"$in": nearby_ids}

    result = await fetch_deals_with_join(db, query)

    if category:
        result = [d for d in result if d["category"] == category.lower()]

    if sort == "price_asc":
        result.sort(key=lambda d: d["price"])
    elif sort == "discount_desc":
        result.sort(key=lambda d: d["price"])
    else:
        result.sort(key=lambda d: d["verified_date"] or "", reverse=True)

    return result


@router.post("/deals/{deal_id}/flag")
async def flag_deal(deal_id: str, request: Request):
    """
    Community quality control: any visitor can flag a deal as incorrect.
    After FLAG_THRESHOLD flags the deal is surfaced in the admin dashboard.
    """
    from bson import ObjectId
    from datetime import datetime

    FLAG_THRESHOLD = 3

    db = get_db()
    try:
        oid = ObjectId(deal_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid deal ID")

    deal = await db.deals.find_one({"_id": oid})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    # Store one flag document per report
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    await db.deal_flags.insert_one({
        "deal_id": oid,
        "ip": client_ip,
        "created_at": datetime.utcnow(),
    })

    flag_count = await db.deal_flags.count_documents({"deal_id": oid})
    if flag_count >= FLAG_THRESHOLD:
        await db.deals.update_one({"_id": oid}, {"$set": {"flagged": True, "flag_count": flag_count}})

    return {"flagged": True, "total_flags": flag_count}
