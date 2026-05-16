from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import datetime
from bson import ObjectId
from ...database import get_db
from ...models import DealCreate, DealUpdate
from ...services.auth import verify_token
from ...utils import fetch_deals_with_join

router = APIRouter()


@router.get("/deals")
async def list_deals(
    sort_by: Optional[str] = Query("verified_date"),
    username: str = Depends(verify_token),
):
    db = get_db()
    result = await fetch_deals_with_join(db, {})

    if sort_by == "store":
        result.sort(key=lambda d: d["vendor_name"].lower())
    elif sort_by == "cut":
        result.sort(key=lambda d: d["cut_name"].lower())
    else:
        result.sort(key=lambda d: d["verified_date"] or "", reverse=True)

    return result


@router.post("/deals", status_code=201)
async def create_deal(body: DealCreate, username: str = Depends(verify_token)):
    db = get_db()

    try:
        vendor_oid = ObjectId(body.vendor_id)
        cut_oid = ObjectId(body.cut_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid vendor_id or cut_id")

    if not await db.vendors.find_one({"_id": vendor_oid}):
        raise HTTPException(status_code=404, detail="Vendor not found")
    if not await db.meat_cuts.find_one({"_id": cut_oid}):
        raise HTTPException(status_code=404, detail="Cut not found")

    now = datetime.utcnow()
    doc = {
        "vendor_id": vendor_oid,
        "cut_id": cut_oid,
        "price": round(float(body.price), 2),
        "price_unit": body.price_unit,
        "verified_date": body.verified_date,
        "sale_end_date": body.sale_end_date,
        "notes": body.notes,
        "active": body.active,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.deals.insert_one(doc)
    created = await db.deals.find_one({"_id": result.inserted_id})
    rows = await fetch_deals_with_join(db, {"_id": result.inserted_id})
    return rows[0] if rows else {"id": str(result.inserted_id)}


@router.put("/deals/{deal_id}")
async def update_deal(deal_id: str, body: DealUpdate, username: str = Depends(verify_token)):
    db = get_db()

    try:
        oid = ObjectId(deal_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid deal ID")

    if not await db.deals.find_one({"_id": oid}):
        raise HTTPException(status_code=404, detail="Deal not found")

    update: dict = {"updated_at": datetime.utcnow()}
    if body.vendor_id is not None:
        update["vendor_id"] = ObjectId(body.vendor_id)
    if body.cut_id is not None:
        update["cut_id"] = ObjectId(body.cut_id)
    if body.price is not None:
        update["price"] = round(float(body.price), 2)
    if body.price_unit is not None:
        update["price_unit"] = body.price_unit
    if body.verified_date is not None:
        update["verified_date"] = body.verified_date
    if body.sale_end_date is not None:
        update["sale_end_date"] = body.sale_end_date
    if body.notes is not None:
        update["notes"] = body.notes
    if body.active is not None:
        update["active"] = body.active

    await db.deals.update_one({"_id": oid}, {"$set": update})
    rows = await fetch_deals_with_join(db, {"_id": oid})
    return rows[0] if rows else {}


@router.delete("/deals/{deal_id}", status_code=204)
async def delete_deal(deal_id: str, username: str = Depends(verify_token)):
    db = get_db()
    try:
        oid = ObjectId(deal_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid deal ID")

    result = await db.deals.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Deal not found")
