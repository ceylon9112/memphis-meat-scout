from fastapi import APIRouter
from ..database import get_db
from ..utils import doc_to_vendor

router = APIRouter()


@router.get("/vendors")
async def list_vendors():
    db = get_db()
    vendors = await db.vendors.find({"active": True}).sort("name", 1).to_list(500)
    return [doc_to_vendor(v) for v in vendors]
