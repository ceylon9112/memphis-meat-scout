from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, date
from bson import ObjectId
from typing import Optional
from pydantic import BaseModel

from ...database import get_db
from ...services.auth import verify_token
from ...services.discovery import run_discovery, get_last_run, is_running
from ...utils import doc_to_vendor, doc_to_cut

router = APIRouter()


def serialize_staged(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "source": doc.get("source"),
        "store_name": doc.get("store_name"),
        "cut_name_raw": doc.get("cut_name_raw"),
        "cut_name_matched": doc.get("cut_name_matched"),
        "match_confidence": doc.get("match_confidence", 0),
        "price": round(float(doc.get("price", 0)), 2),
        "price_unit": doc.get("price_unit", "per_lb"),
        "found_date": doc.get("found_date"),
        "status": doc.get("status", "pending"),
        "source_data": doc.get("source_data", {}),
        "created_at": doc.get("created_at"),
    }


class ApproveRequest(BaseModel):
    vendor_id: str
    cut_id: str
    price: float
    price_unit: str
    verified_date: Optional[str] = None
    notes: Optional[str] = None


@router.get("/staging/status")
async def staging_status(username: str = Depends(verify_token)):
    db = get_db()
    pending = await db.staged_deals.count_documents({"status": "pending"})
    last_run = get_last_run()
    return {
        "pending": pending,
        "running": is_running(),
        "last_run": last_run.isoformat() if last_run else None,
    }


@router.get("/staging")
async def list_staged(
    status: Optional[str] = "pending",
    username: str = Depends(verify_token),
):
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    docs = await db.staged_deals.find(query).to_list(500)
    docs.sort(key=lambda d: d.get("created_at", ""), reverse=True)
    return [serialize_staged(d) for d in docs]


@router.post("/staging/run")
async def trigger_discovery(username: str = Depends(verify_token)):
    if is_running():
        return {"status": "already_running"}
    result = await run_discovery()
    return result


@router.post("/staging/auto-approve")
async def bulk_auto_approve(username: str = Depends(verify_token)):
    """Immediately promote all pending staged deals that meet the confidence threshold."""
    from ...services.discovery import auto_approve_pending
    db = get_db()
    approved = await auto_approve_pending(db)
    remaining = await db.staged_deals.count_documents({"status": "pending"})
    return {"auto_approved": approved, "still_pending": remaining}


@router.post("/staging/{staged_id}/approve", status_code=201)
async def approve_staged(
    staged_id: str,
    body: ApproveRequest,
    username: str = Depends(verify_token),
):
    db = get_db()
    try:
        oid = ObjectId(staged_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

    staged = await db.staged_deals.find_one({"_id": oid})
    if not staged:
        raise HTTPException(status_code=404, detail="Staged deal not found")

    try:
        vendor_oid = ObjectId(body.vendor_id)
        cut_oid = ObjectId(body.cut_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid vendor_id or cut_id")

    now = datetime.utcnow()
    deal = {
        "vendor_id": vendor_oid,
        "cut_id": cut_oid,
        "price": round(float(body.price), 2),
        "price_unit": body.price_unit,
        "verified_date": body.verified_date or date.today().isoformat(),
        "sale_end_date": staged.get("sale_end_date"),
        "notes": body.notes or f"Auto-discovered via {staged.get('source', 'unknown')} ({staged.get('store_name', '')})",
        "active": True,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.deals.insert_one(deal)

    await db.staged_deals.update_one(
        {"_id": oid},
        {"$set": {"status": "approved", "approved_deal_id": str(result.inserted_id)}}
    )
    return {"status": "approved", "deal_id": str(result.inserted_id)}


@router.post("/staging/{staged_id}/dismiss")
async def dismiss_staged(staged_id: str, username: str = Depends(verify_token)):
    db = get_db()
    try:
        oid = ObjectId(staged_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

    result = await db.staged_deals.update_one(
        {"_id": oid, "status": "pending"},
        {"$set": {"status": "dismissed"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Staged deal not found or already processed")
    return {"status": "dismissed"}


@router.delete("/staging/dismissed")
async def clear_dismissed(username: str = Depends(verify_token)):
    db = get_db()
    result = await db.staged_deals.delete_many({"status": "dismissed"})
    return {"deleted": result.deleted_count}
