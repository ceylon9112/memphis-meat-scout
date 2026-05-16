from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from bson import ObjectId
from ...database import get_db
from ...models import VendorCreate, VendorUpdate
from ...services.auth import verify_token
from ...utils import doc_to_vendor

router = APIRouter()


@router.get("/vendors")
async def list_vendors(username: str = Depends(verify_token)):
    db = get_db()
    vendors = await db.vendors.find({}).to_list(500)
    vendors.sort(key=lambda v: v.get("name", "").lower())
    return [doc_to_vendor(v) for v in vendors]


@router.post("/vendors", status_code=201)
async def create_vendor(body: VendorCreate, username: str = Depends(verify_token)):
    db = get_db()
    doc = {**body.model_dump(), "created_at": datetime.utcnow()}
    result = await db.vendors.insert_one(doc)
    created = await db.vendors.find_one({"_id": result.inserted_id})
    return doc_to_vendor(created)


@router.put("/vendors/{vendor_id}")
async def update_vendor(vendor_id: str, body: VendorUpdate, username: str = Depends(verify_token)):
    db = get_db()
    try:
        oid = ObjectId(vendor_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid vendor ID")

    if not await db.vendors.find_one({"_id": oid}):
        raise HTTPException(status_code=404, detail="Vendor not found")

    update = {k: v for k, v in body.model_dump().items() if v is not None or k == "featured"}
    await db.vendors.update_one({"_id": oid}, {"$set": update})
    updated = await db.vendors.find_one({"_id": oid})
    return doc_to_vendor(updated)
