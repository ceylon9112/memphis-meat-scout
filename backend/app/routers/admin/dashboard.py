from fastapi import APIRouter, Depends
from datetime import date, timedelta
from ...database import get_db
from ...services.auth import verify_token

router = APIRouter()


def active_cutoff() -> str:
    return (date.today() - timedelta(days=6)).isoformat()


def expiring_range() -> tuple:
    today = date.today()
    low = (today - timedelta(days=7)).isoformat()
    high = (today - timedelta(days=5)).isoformat()  # 5, 6, or 7 days ago
    return low, high


@router.get("/dashboard")
async def dashboard(username: str = Depends(verify_token)):
    db = get_db()
    cutoff = active_cutoff()
    stale_cutoff = (date.today() - timedelta(days=7)).isoformat()
    exp_low, exp_high = expiring_range()

    active_deals = await db.deals.count_documents(
        {"active": True, "verified_date": {"$gte": cutoff}}
    )
    expiring_soon = await db.deals.count_documents(
        {"active": True, "verified_date": {"$gte": exp_low, "$lte": exp_high}}
    )
    stale_deals = await db.deals.count_documents(
        {"active": True, "verified_date": {"$lt": cutoff}}
    )
    active_vendors = await db.vendors.count_documents({"active": True})

    return {
        "active_deals": active_deals,
        "expiring_soon": expiring_soon,
        "stale_deals": stale_deals,
        "active_vendors": active_vendors,
    }
