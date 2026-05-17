from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, date
from bson import ObjectId
from typing import Optional
from pydantic import BaseModel

from ...database import get_db
from ...services.auth import verify_token
from ...services.discovery import run_discovery, get_last_run, is_running, auto_approve_pending
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
        "sale_end_date": doc.get("sale_end_date"),
        "source_zip": doc.get("source_zip"),
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


class ActivateVendorRequest(BaseModel):
    stub_id: str
    name: str
    city: str
    state: str
    type: str
    zip_code: Optional[str] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


# ─── Status ───────────────────────────────────────────────────────────────────

@router.get("/staging/status")
async def staging_status(username: str = Depends(verify_token)):
    db = get_db()
    pending       = await db.staged_deals.count_documents({"status": "pending"})
    vendor_pend   = await db.staged_deals.count_documents({"status": "vendor_pending"})
    new_stores    = await db.vendors.count_documents({"auto_created": True})
    last_run      = get_last_run()
    return {
        "pending": pending,
        "vendor_pending": vendor_pend,
        "new_stores": new_stores,
        "running": is_running(),
        "last_run": last_run.isoformat() if last_run else None,
    }


# ─── Staged deal list ─────────────────────────────────────────────────────────

@router.get("/staging")
async def list_staged(
    status: Optional[str] = "pending",
    min_confidence: Optional[float] = None,
    max_confidence: Optional[float] = None,
    username: str = Depends(verify_token),
):
    db = get_db()
    query: dict = {}
    if status:
        query["status"] = status
    docs = await db.staged_deals.find(query).to_list(1000)
    docs.sort(key=lambda d: d.get("match_confidence", 0), reverse=True)

    results = [serialize_staged(d) for d in docs]
    if min_confidence is not None:
        results = [r for r in results if r["match_confidence"] >= min_confidence]
    if max_confidence is not None:
        results = [r for r in results if r["match_confidence"] <= max_confidence]
    return results


# ─── Trigger discovery ────────────────────────────────────────────────────────

@router.post("/staging/run")
async def trigger_discovery(username: str = Depends(verify_token)):
    if is_running():
        return {"status": "already_running"}
    result = await run_discovery()
    return result


@router.post("/staging/auto-approve")
async def bulk_auto_approve(username: str = Depends(verify_token)):
    """Re-run auto-approval pass over all current pending staged deals."""
    db = get_db()
    approved = await auto_approve_pending(db)
    remaining = await db.staged_deals.count_documents({"status": "pending"})
    return {"auto_approved": approved, "still_pending": remaining}


# ─── New stores (vendor stubs) ────────────────────────────────────────────────

@router.get("/staging/new-stores")
async def list_new_stores(username: str = Depends(verify_token)):
    """Return auto-created vendor stubs with their pending deal counts."""
    db = get_db()
    stubs = await db.vendors.find({"auto_created": True}).to_list(200)
    result = []
    for stub in stubs:
        deal_count = await db.staged_deals.count_documents({
            "store_name": stub["name"],
            "status": {"$in": ["vendor_pending", "pending"]},
        })
        result.append({
            "id": str(stub["_id"]),
            "name": stub["name"],
            "city": stub.get("city", ""),
            "state": stub.get("state", ""),
            "type": stub.get("type", "chain"),
            "zip_code": stub.get("zip_code"),
            "deal_count": deal_count,
            "created_at": stub.get("created_at"),
        })
    result.sort(key=lambda s: s["deal_count"], reverse=True)
    return result


@router.post("/staging/activate-vendor")
async def activate_vendor_stub(
    body: ActivateVendorRequest,
    username: str = Depends(verify_token),
):
    """
    Activate a vendor stub: updates the record, marks it active, then
    re-runs auto-approval so all its vendor_pending deals go live.
    """
    db = get_db()
    try:
        oid = ObjectId(body.stub_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid stub ID")

    stub = await db.vendors.find_one({"_id": oid})
    if not stub:
        raise HTTPException(status_code=404, detail="Vendor stub not found")

    original_name = stub["name"]

    update: dict = {
        "name": body.name,
        "city": body.city,
        "state": body.state,
        "type": body.type,
        "active": True,
        "auto_created": False,
    }
    if body.zip_code is not None:
        update["zip_code"] = body.zip_code
    if body.address is not None:
        update["address"] = body.address
    if body.lat is not None:
        update["lat"] = body.lat
    if body.lng is not None:
        update["lng"] = body.lng

    await db.vendors.update_one({"_id": oid}, {"$set": update})

    # Re-queue vendor_pending deals so auto_approve can pick them up
    for sn in {original_name, body.name}:
        await db.staged_deals.update_many(
            {"store_name": sn, "status": "vendor_pending"},
            {"$set": {"status": "pending"}},
        )

    approved = await auto_approve_pending(db)
    return {"activated": True, "auto_approved": approved}


@router.delete("/staging/new-stores/{stub_id}")
async def dismiss_vendor_stub(stub_id: str, username: str = Depends(verify_token)):
    """Delete a vendor stub and dismiss all its associated pending deals."""
    db = get_db()
    try:
        oid = ObjectId(stub_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid stub ID")

    stub = await db.vendors.find_one({"_id": oid, "auto_created": True})
    if not stub:
        raise HTTPException(status_code=404, detail="Stub not found")

    store_name = stub["name"]
    await db.vendors.delete_one({"_id": oid})
    await db.staged_deals.update_many(
        {"store_name": store_name, "status": {"$in": ["vendor_pending", "pending"]}},
        {"$set": {"status": "dismissed"}},
    )
    return {"dismissed": True}


# ─── Per-deal actions ─────────────────────────────────────────────────────────

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
        cut_oid    = ObjectId(body.cut_id)
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
        "notes": body.notes or f"Manually approved · {staged.get('source', 'unknown')} · {staged.get('store_name', '')}",
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
        {"_id": oid, "status": {"$in": ["pending", "vendor_pending"]}},
        {"$set": {"status": "dismissed"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Staged deal not found or already processed")
    return {"status": "dismissed"}


@router.post("/staging/bulk-dismiss")
async def bulk_dismiss(
    body: dict,
    username: str = Depends(verify_token),
):
    """
    Dismiss multiple staged deals at once.
    Body: { "ids": [...] }  OR  { "max_confidence": 0.5 }
    """
    db = get_db()
    query: dict = {"status": "pending"}

    if "ids" in body:
        try:
            oids = [ObjectId(i) for i in body["ids"]]
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid ID in list")
        query["_id"] = {"$in": oids}
    elif "max_confidence" in body:
        query["match_confidence"] = {"$lte": float(body["max_confidence"])}
    else:
        raise HTTPException(status_code=400, detail="Provide 'ids' or 'max_confidence'")

    result = await db.staged_deals.update_many(query, {"$set": {"status": "dismissed"}})
    return {"dismissed": result.modified_count}


@router.delete("/staging/dismissed")
async def clear_dismissed(username: str = Depends(verify_token)):
    db = get_db()
    result = await db.staged_deals.delete_many({"status": "dismissed"})
    return {"deleted": result.deleted_count}
