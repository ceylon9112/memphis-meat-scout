from bson import ObjectId
from datetime import datetime


def doc_to_vendor(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "city": doc["city"],
        "state": doc["state"],
        "type": doc["type"],
        "active": doc["active"],
        "created_at": doc["created_at"],
    }


def doc_to_cut(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "category": doc["category"],
        "active": doc["active"],
        "created_at": doc["created_at"],
    }


def doc_to_deal(doc: dict, vendor_map: dict, cut_map: dict) -> dict:
    vid = str(doc.get("vendor_id", ""))
    cid = str(doc.get("cut_id", ""))
    vendor = vendor_map.get(vid, {})
    cut = cut_map.get(cid, {})
    return {
        "id": str(doc["_id"]),
        "vendor_id": vid,
        "cut_id": cid,
        "vendor_name": vendor.get("name", "Unknown"),
        "cut_name": cut.get("name", "Unknown"),
        "category": cut.get("category", ""),
        "price": round(float(doc.get("price", 0)), 2),
        "price_unit": doc.get("price_unit"),
        "verified_date": doc.get("verified_date"),
        "sale_end_date": doc.get("sale_end_date"),
        "notes": doc.get("notes"),
        "active": doc.get("active", True),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


async def fetch_deals_with_join(db, query: dict) -> list:
    deals = await db.deals.find(query).to_list(2000)
    if not deals:
        return []

    vendor_oids = list({d["vendor_id"] for d in deals if "vendor_id" in d})
    cut_oids = list({d["cut_id"] for d in deals if "cut_id" in d})

    vendors = await db.vendors.find({"_id": {"$in": vendor_oids}}).to_list(500)
    cuts = await db.meat_cuts.find({"_id": {"$in": cut_oids}}).to_list(500)

    vendor_map = {str(v["_id"]): v for v in vendors}
    cut_map = {str(c["_id"]): c for c in cuts}

    return [doc_to_deal(d, vendor_map, cut_map) for d in deals]
