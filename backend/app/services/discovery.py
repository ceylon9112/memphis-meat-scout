"""
Discovery orchestrator: runs all sources, deduplicates, and writes to the
staged_deals collection for admin review.

High-confidence matches (>= AUTO_APPROVE_THRESHOLD) are promoted directly
to the live deals collection without requiring manual approval.

Unknown stores get a vendor stub created automatically (active=False) so
the admin can review and activate them from the staging panel — no manual
vendor additions needed.

Flipp runs for every market zip code in MARKET_ZIPS so that chain stores
across all configured markets are automatically discovered.
"""
import asyncio
import httpx
from datetime import datetime, date
from difflib import SequenceMatcher

from ..database import get_db
from .kroger import fetch_kroger_deals
from .flipp import fetch_flipp_deals
from .ramons import fetch_ramons_deals
from .traderjoes import fetch_traderjoes_deals
from .wholefoods import fetch_wholefoods_deals
from .freshmarket import fetch_freshmarket_deals
from .cut_matcher import is_price_sane

_last_run: datetime | None = None
_running: bool = False

AUTO_APPROVE_THRESHOLD = 0.30   # publish-first: user flagging handles quality control

# One representative zip per market — Flipp covers all stores within ~25 mi
MARKET_ZIPS = [
    "38103",  # Memphis, TN (downtown)
    "38138",  # Germantown, TN
    "37201",  # Nashville, TN
    "35203",  # Birmingham, AL
    "72201",  # Little Rock, AR
    "39201",  # Jackson, MS
    "37902",  # Knoxville, TN
    "36608",  # Mobile, AL
]

# Cache: zip → (city, state abbreviation)
_location_cache: dict[str, tuple[str, str]] = {
    "38103": ("Memphis", "TN"),
    "38138": ("Germantown", "TN"),
    "37201": ("Nashville", "TN"),
    "35203": ("Birmingham", "AL"),
    "72201": ("Little Rock", "AR"),
    "39201": ("Jackson", "MS"),
    "37902": ("Knoxville", "TN"),
    "36608": ("Mobile", "AL"),
}


async def _zip_to_location(zip_code: str) -> tuple[str, str]:
    """Return (city, state_abbr) for a US zip using the free zippopotam.us API."""
    if zip_code in _location_cache:
        return _location_cache[zip_code]
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"https://api.zippopotam.us/us/{zip_code}")
            if resp.status_code == 200:
                place = resp.json()["places"][0]
                result = place["place name"], place["state abbreviation"]
                _location_cache[zip_code] = result
                return result
    except Exception:
        pass
    return ("Unknown", "TN")


async def _find_vendor(db, store_name: str, source_zip: str | None = None) -> dict | None:
    """
    Resolve a store name to a vendor document using a three-step strategy:

    1. Exact name match, city-preferred (city inferred from source_zip)
    2. Prefix / starts-with match (handles "Kroger #5421" → "Kroger")
    3. Fuzzy ratio match (≥ 0.72) as a final fallback
    """
    active_vendors = await db.vendors.find({"active": True, "auto_created": {"$ne": True}}).to_list(1000)
    if not active_vendors:
        return None

    store_lower = store_name.lower().strip()

    # Infer city from source zip for disambiguation
    preferred_city: str | None = None
    if source_zip:
        city, _ = await _zip_to_location(source_zip)
        preferred_city = city.lower() if city != "Unknown" else None

    def _score(v: dict) -> float:
        vname = v["name"].lower().strip()
        # Exact name
        if vname == store_lower:
            return 2.0 if (preferred_city and v.get("city", "").lower() == preferred_city) else 1.9
        # Store name starts with vendor name (e.g. "Kroger #5421" → "Kroger")
        if store_lower.startswith(vname) or vname.startswith(store_lower):
            return 1.5 if (preferred_city and v.get("city", "").lower() == preferred_city) else 1.4
        # Token overlap: vendor tokens all appear in store name
        vtokens = set(vname.split())
        stokens = set(store_lower.split())
        if vtokens and vtokens.issubset(stokens):
            return 1.2 if (preferred_city and v.get("city", "").lower() == preferred_city) else 1.1
        # Fuzzy ratio
        ratio = SequenceMatcher(None, store_lower, vname).ratio()
        return ratio

    best = max(active_vendors, key=_score)
    best_score = _score(best)

    # Accept if: exact/prefix hit (score ≥ 1.1) or fuzzy ratio ≥ 0.72
    if best_score >= 1.1 or best_score >= 0.72:
        return best
    return None


async def auto_approve_pending(db) -> int:
    """
    Scan all pending staged deals and promote high-confidence ones to live deals.
    For unknown stores, auto-create a vendor stub so the admin can activate them.
    Returns the number of deals newly approved.
    """
    today = date.today().isoformat()
    now = datetime.utcnow()
    approved = 0

    pending = await db.staged_deals.find({"status": "pending"}).to_list(2000)

    for doc in pending:
        if doc.get("match_confidence", 0) < AUTO_APPROVE_THRESHOLD:
            continue

        source_zip = doc.get("source_zip")
        vendor = await _find_vendor(db, doc["store_name"], source_zip)

        if not vendor:
            # Auto-create AND immediately activate a vendor stub.
            # The store passed the FOOD_MERCHANTS filter so it's a real food retailer.
            existing = await db.vendors.find_one({"name": doc["store_name"]})
            if existing:
                vendor = existing
            else:
                city, state = await _zip_to_location(source_zip or "38103")
                stub = {
                    "name": doc["store_name"],
                    "city": city,
                    "state": state,
                    "type": "chain",
                    "active": True,          # publish immediately
                    "featured": False,
                    "auto_created": True,
                    "zip_code": source_zip,
                    "created_at": now,
                }
                result_v = await db.vendors.insert_one(stub)
                vendor = await db.vendors.find_one({"_id": result_v.inserted_id})

        # Resolve cut
        cut = await db.meat_cuts.find_one({"name": doc["cut_name_matched"], "active": True})
        if not cut:
            cut = await db.meat_cuts.find_one({
                "name": {"$regex": f"^{doc['cut_name_matched']}$", "$options": "i"},
                "active": True,
            })
        if not cut:
            continue

        # Price sanity check — skip obvious scraping errors
        price_unit = doc.get("price_unit", "per_lb")
        price_val  = round(float(doc["price"]), 2)
        if not is_price_sane(doc["cut_name_matched"], price_val, price_unit):
            await db.staged_deals.update_one(
                {"_id": doc["_id"]},
                {"$set": {"status": "price_flagged"}},
            )
            continue

        # Skip if identical deal already active today
        existing_deal = await db.deals.find_one({
            "vendor_id": vendor["_id"],
            "cut_id": cut["_id"],
            "active": True,
            "verified_date": doc.get("found_date") or today,
        })
        if existing_deal:
            await db.staged_deals.update_one(
                {"_id": doc["_id"]},
                {"$set": {"status": "approved", "approved_deal_id": str(existing_deal["_id"])}},
            )
            continue

        deal = {
            "vendor_id": vendor["_id"],
            "cut_id": cut["_id"],
            "price": price_val,
            "price_unit": price_unit,
            "verified_date": doc.get("found_date") or today,
            "sale_end_date": doc.get("sale_end_date"),
            "notes": (
                f"Auto-approved ({doc['match_confidence']:.0%} confidence) · "
                f"{doc.get('source', '')} · {doc.get('store_name', '')}"
            ),
            "active": True,
            "created_at": now,
            "updated_at": now,
        }
        result = await db.deals.insert_one(deal)
        await db.staged_deals.update_one(
            {"_id": doc["_id"]},
            {"$set": {"status": "approved", "approved_deal_id": str(result.inserted_id)}},
        )
        approved += 1

    return approved


async def run_discovery() -> dict:
    """
    Pull from all configured sources, deduplicate, stage new candidates,
    then auto-approve high-confidence ones.
    """
    global _last_run, _running
    if _running:
        return {"status": "already_running"}

    _running = True
    summary = {
        "flipp": 0, "ramons": 0, "traderjoes": 0, "wholefoods": 0,
        "freshmarket": 0, "kroger": 0, "skipped_duplicates": 0,
        "auto_approved": 0, "vendor_stubs_created": 0,
        "errors": [], "markets_scanned": len(MARKET_ZIPS),
    }

    try:
        today = date.today().isoformat()
        db = get_db()

        kroger_task  = asyncio.create_task(fetch_kroger_deals())
        ramons_task  = asyncio.create_task(fetch_ramons_deals())
        tj_task      = asyncio.create_task(fetch_traderjoes_deals())
        wf_task      = asyncio.create_task(fetch_wholefoods_deals())
        fm_task      = asyncio.create_task(fetch_freshmarket_deals())
        flipp_tasks  = [asyncio.create_task(fetch_flipp_deals(z)) for z in MARKET_ZIPS]

        kroger_results, ramons_results, tj_results, wf_results, fm_results, *flipp_lists = \
            await asyncio.gather(
                kroger_task, ramons_task, tj_task, wf_task, fm_task, *flipp_tasks,
                return_exceptions=True,
            )

        if isinstance(kroger_results, Exception): summary["errors"].append(f"Kroger: {kroger_results}");     kroger_results = []
        if isinstance(ramons_results, Exception): summary["errors"].append(f"Ramon's: {ramons_results}");    ramons_results = []
        if isinstance(tj_results,     Exception): summary["errors"].append(f"Trader Joe's: {tj_results}");  tj_results     = []
        if isinstance(wf_results,     Exception): summary["errors"].append(f"Whole Foods: {wf_results}");   wf_results     = []
        if isinstance(fm_results,     Exception): summary["errors"].append(f"Fresh Market: {fm_results}");  fm_results     = []

        flipp_results: list[dict] = []
        for i, fl in enumerate(flipp_lists):
            if isinstance(fl, Exception):
                summary["errors"].append(f"Flipp ({MARKET_ZIPS[i]}): {fl}")
            else:
                flipp_results.extend(fl)

        all_candidates = kroger_results + flipp_results + ramons_results + tj_results + wf_results + fm_results

        # Deduplicate against deals already staged today
        existing = await db.staged_deals.find(
            {"found_date": today}, {"source": 1, "cut_name_raw": 1, "price": 1}
        ).to_list(5000)
        existing_keys = {
            f"{d['source']}:{d['cut_name_raw'].lower()}:{d['price']}"
            for d in existing
        }

        to_insert = []
        for candidate in all_candidates:
            key = f"{candidate['source']}:{candidate['cut_name_raw'].lower()}:{candidate['price']}"
            if key in existing_keys:
                summary["skipped_duplicates"] += 1
                continue
            existing_keys.add(key)
            to_insert.append({
                **candidate,
                "found_date": today,
                "status": "pending",
                "created_at": datetime.utcnow(),
            })

        if to_insert:
            await db.staged_deals.insert_many(to_insert)

        for doc in to_insert:
            summary[doc["source"]] = summary.get(doc["source"], 0) + 1

        stubs_before = await db.vendors.count_documents({"auto_created": True})
        summary["auto_approved"] = await auto_approve_pending(db)
        stubs_after = await db.vendors.count_documents({"auto_created": True})
        summary["vendor_stubs_created"] = stubs_after - stubs_before

        _last_run = datetime.utcnow()
        summary["status"] = "ok"
        summary["total_new"] = len(to_insert)

    except Exception as e:
        summary["status"] = "error"
        summary["errors"].append(str(e))
    finally:
        _running = False

    return summary


def get_last_run() -> datetime | None:
    return _last_run


def is_running() -> bool:
    return _running
