"""
Discovery orchestrator: runs all sources, deduplicates, and writes to the
staged_deals collection for admin review.
"""
import asyncio
from datetime import datetime, date

from ..database import get_db
from .kroger import fetch_kroger_deals
from .flipp import fetch_flipp_deals
from .ramons import fetch_ramons_deals
from .traderjoes import fetch_traderjoes_deals
from .wholefoods import fetch_wholefoods_deals
from .freshmarket import fetch_freshmarket_deals

_last_run: datetime | None = None
_running: bool = False


async def run_discovery() -> dict:
    """
    Pull from all configured sources, deduplicate against recent staged deals,
    and insert new candidates into the staged_deals collection.
    Returns a summary dict.

    Sources:
    - Flipp/Wishabi: weekly ad flyers — Kroger, ALDI, Walmart, Superlo, Sprouts, Costco, etc.
    - Ramon's Meat Market: live prices from ramonsmeatmarket.com (Wix store).
    - Trader Joe's: everyday prices from the TJ GraphQL API (Germantown TN store).
    - Whole Foods Market: weekly sale prices via iweeklyads.com circular aggregator.
    - The Fresh Market: weekly specials from homepage __NEXT_DATA__ JSON (Germantown + 2x Memphis).
    - Kroger Developer API: optional real-time prices (requires API key in .env).
    """
    global _last_run, _running
    if _running:
        return {"status": "already_running"}

    _running = True
    summary = {
        "flipp": 0, "ramons": 0, "traderjoes": 0, "wholefoods": 0,
        "freshmarket": 0, "kroger": 0, "skipped_duplicates": 0, "errors": [],
    }

    try:
        today = date.today().isoformat()
        db = get_db()

        # Fetch from all sources concurrently
        # TJ runs sequentially with delays internally, others run fully parallel
        kroger_task = asyncio.create_task(fetch_kroger_deals())
        flipp_task = asyncio.create_task(fetch_flipp_deals())
        ramons_task = asyncio.create_task(fetch_ramons_deals())
        tj_task = asyncio.create_task(fetch_traderjoes_deals())
        wf_task = asyncio.create_task(fetch_wholefoods_deals())
        fm_task = asyncio.create_task(fetch_freshmarket_deals())

        kroger_results, flipp_results, ramons_results, tj_results, wf_results, fm_results = await asyncio.gather(
            kroger_task, flipp_task, ramons_task, tj_task, wf_task, fm_task,
            return_exceptions=True,
        )

        if isinstance(kroger_results, Exception):
            summary["errors"].append(f"Kroger API: {kroger_results}")
            kroger_results = []
        if isinstance(flipp_results, Exception):
            summary["errors"].append(f"Flipp: {flipp_results}")
            flipp_results = []
        if isinstance(ramons_results, Exception):
            summary["errors"].append(f"Ramon's: {ramons_results}")
            ramons_results = []
        if isinstance(tj_results, Exception):
            summary["errors"].append(f"Trader Joe's: {tj_results}")
            tj_results = []
        if isinstance(wf_results, Exception):
            summary["errors"].append(f"Whole Foods: {wf_results}")
            wf_results = []
        if isinstance(fm_results, Exception):
            summary["errors"].append(f"Fresh Market: {fm_results}")
            fm_results = []

        all_candidates = kroger_results + flipp_results + ramons_results + tj_results + wf_results + fm_results

        # Build dedup key set from deals already staged today
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
            doc = {
                **candidate,
                "found_date": today,
                "status": "pending",
                "created_at": datetime.utcnow(),
            }
            to_insert.append(doc)

        if to_insert:
            await db.staged_deals.insert_many(to_insert)

        for doc in to_insert:
            summary[doc["source"]] = summary.get(doc["source"], 0) + 1

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
