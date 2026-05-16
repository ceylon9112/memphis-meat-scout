from fastapi import APIRouter
from ..database import get_db
from ..utils import doc_to_vendor

router = APIRouter()


@router.get("/vendors")
async def list_vendors():
    db = get_db()
    vendors = await db.vendors.find({"active": True}).to_list(500)
    vendors.sort(key=lambda v: v.get("name", "").lower())
    return [doc_to_vendor(v) for v in vendors]
