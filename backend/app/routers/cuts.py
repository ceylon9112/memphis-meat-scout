from fastapi import APIRouter
from ..database import get_db
from ..utils import doc_to_cut, fetch_deals_with_join
from datetime import date, timedelta

router = APIRouter()


@router.get("/cuts")
async def list_cuts():
    db = get_db()
    cuts = await db.meat_cuts.find({"active": True}).to_list(500)
    cuts.sort(key=lambda c: c.get("name", "").lower())
    return [doc_to_cut(c) for c in cuts]


@router.get("/cuts/{cut_id}/prices")
async def cut_prices(cut_id: str):
    from bson import ObjectId

    db = get_db()

    try:
        cut_oid = ObjectId(cut_id)
    except Exception:
        return []

    cut = await db.meat_cuts.find_one({"_id": cut_oid, "active": True})
    if not cut:
        return []

    cutoff = (date.today() - timedelta(days=6)).isoformat()
    query = {"active": True, "verified_date": {"$gte": cutoff}, "cut_id": cut_oid}
    result = await fetch_deals_with_join(db, query)
    result.sort(key=lambda d: d["price"])
    return result
