from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from bson import ObjectId
from ...database import get_db
from ...models import MeatCutCreate, MeatCutUpdate
from ...services.auth import verify_token
from ...utils import doc_to_cut

router = APIRouter()


@router.get("/cuts")
async def list_cuts(username: str = Depends(verify_token)):
    db = get_db()
    cuts = await db.meat_cuts.find({}).sort("name", 1).to_list(500)
    return [doc_to_cut(c) for c in cuts]


@router.post("/cuts", status_code=201)
async def create_cut(body: MeatCutCreate, username: str = Depends(verify_token)):
    db = get_db()
    doc = {**body.model_dump(), "created_at": datetime.utcnow()}
    result = await db.meat_cuts.insert_one(doc)
    created = await db.meat_cuts.find_one({"_id": result.inserted_id})
    return doc_to_cut(created)


@router.put("/cuts/{cut_id}")
async def update_cut(cut_id: str, body: MeatCutUpdate, username: str = Depends(verify_token)):
    db = get_db()
    try:
        oid = ObjectId(cut_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid cut ID")

    if not await db.meat_cuts.find_one({"_id": oid}):
        raise HTTPException(status_code=404, detail="Cut not found")

    update = {k: v for k, v in body.model_dump().items() if v is not None}
    await db.meat_cuts.update_one({"_id": oid}, {"$set": update})
    updated = await db.meat_cuts.find_one({"_id": oid})
    return doc_to_cut(updated)
