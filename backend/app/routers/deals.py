from fastapi import APIRouter, Query
from typing import Optional
from datetime import date, timedelta
from ..database import get_db
from ..utils import fetch_deals_with_join

router = APIRouter()


def active_cutoff() -> str:
    return (date.today() - timedelta(days=6)).isoformat()


@router.get("/deals")
async def list_deals(
    category: Optional[str] = Query(None),
    vendor_id: Optional[str] = Query(None),
    cut_id: Optional[str] = Query(None),
    sort: Optional[str] = Query("recent"),
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
