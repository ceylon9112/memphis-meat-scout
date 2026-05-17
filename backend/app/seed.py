from datetime import datetime
from bson import ObjectId
from .database import get_db
from .services.auth import hash_password
import os


# ── One record per brand. City = primary / most relevant location. ────────────
# fmt: off
VENDOR_SEED = [
    # ── Memphis, TN — local & specialty ──────────────────────────────────────
    {"name": "Ramon's Meat Market",
     "city": "Memphis", "state": "TN", "type": "independent",
     "zip_code": "38116", "lat": 35.059, "lng": -90.010,
     "address": "4191 Elvis Presley Blvd"},
    {"name": "Southern Meat Market",
     "city": "Memphis", "state": "TN", "type": "independent",
     "zip_code": "38104", "lat": 35.145, "lng": -90.038},
    {"name": "Gordin's",
     "city": "Memphis", "state": "TN", "type": "independent",
     "zip_code": "38104", "lat": 35.145, "lng": -90.040,
     "address": "1161 Union Ave"},
    {"name": "Fayette Packing",
     "city": "Somerville", "state": "TN", "type": "specialty",
     "zip_code": "38068", "lat": 35.246, "lng": -89.358},
    {"name": "Gordon Food Service",
     "city": "Memphis", "state": "TN", "type": "wholesale",
     "zip_code": "38116", "lat": 35.062, "lng": -90.028},
    {"name": "Restaurant Depot",
     "city": "Memphis", "state": "TN", "type": "wholesale",
     "zip_code": "38103", "lat": 35.151, "lng": -90.046},
    {"name": "Gene Stimson Big Star",
     "city": "Memphis", "state": "TN", "type": "chain",
     "zip_code": "38118", "lat": 35.080, "lng": -89.930},
    {"name": "Superlo Foods",
     "city": "Memphis", "state": "TN", "type": "chain",
     "zip_code": "38116", "lat": 35.065, "lng": -90.003},
    {"name": "Market Place",
     "city": "Memphis", "state": "TN", "type": "chain",
     "zip_code": "38103", "lat": 35.149, "lng": -90.048},

    # ── National / regional chains ────────────────────────────────────────────
    {"name": "Kroger",
     "city": "Memphis", "state": "TN", "type": "chain",
     "zip_code": "38118", "lat": 35.072, "lng": -89.940},
    {"name": "ALDI",
     "city": "Memphis", "state": "TN", "type": "chain",
     "zip_code": "38115", "lat": 35.097, "lng": -89.895},
    {"name": "Walmart",
     "city": "Memphis", "state": "TN", "type": "chain",
     "zip_code": "38128", "lat": 35.226, "lng": -89.946},
    {"name": "Sam's Club",
     "city": "Memphis", "state": "TN", "type": "wholesale",
     "zip_code": "38128", "lat": 35.221, "lng": -89.945},
    {"name": "Costco",
     "city": "Memphis", "state": "TN", "type": "chain",
     "zip_code": "38138", "lat": 35.087, "lng": -89.791},
    {"name": "Target",
     "city": "Memphis", "state": "TN", "type": "chain",
     "zip_code": "38119", "lat": 35.094, "lng": -89.849},
    {"name": "Sprouts Farmers Market",
     "city": "Memphis", "state": "TN", "type": "chain",
     "zip_code": "38120", "lat": 35.120, "lng": -89.853},
    {"name": "Save A Lot",
     "city": "Memphis", "state": "TN", "type": "chain",
     "zip_code": "38106", "lat": 35.103, "lng": -90.043},
    {"name": "Piggly Wiggly",
     "city": "Memphis", "state": "TN", "type": "chain",
     "zip_code": "38106", "lat": 35.103, "lng": -90.044},
    {"name": "Food Lion",
     "city": "Knoxville", "state": "TN", "type": "chain",
     "zip_code": "37917", "lat": 35.990, "lng": -83.940},
    {"name": "Winn-Dixie",
     "city": "Mobile", "state": "AL", "type": "chain",
     "zip_code": "36606", "lat": 30.681, "lng": -88.083},
    {"name": "Publix",
     "city": "Nashville", "state": "TN", "type": "chain",
     "zip_code": "37215", "lat": 36.100, "lng": -86.835},
    {"name": "Food City",
     "city": "Knoxville", "state": "TN", "type": "chain",
     "zip_code": "37917", "lat": 35.988, "lng": -83.937},
    {"name": "Natural Grocers",
     "city": "Little Rock", "state": "AR", "type": "chain",
     "zip_code": "72205", "lat": 34.739, "lng": -92.361},
    {"name": "Western Supermarkets",
     "city": "Birmingham", "state": "AL", "type": "independent",
     "zip_code": "35209", "lat": 33.479, "lng": -86.818},

    # ── Premium / specialty chains ────────────────────────────────────────────
    {"name": "Trader Joe's",
     "city": "Germantown", "state": "TN", "type": "chain",
     "zip_code": "38138", "lat": 35.088, "lng": -89.803},
    {"name": "Whole Foods Market",
     "city": "Germantown", "state": "TN", "type": "chain",
     "zip_code": "38138", "lat": 35.089, "lng": -89.805},
    {"name": "The Fresh Market",
     "city": "Germantown", "state": "TN", "type": "chain",
     "zip_code": "38138", "lat": 35.087, "lng": -89.800},

    # ── Gulf Coast / Alabama ──────────────────────────────────────────────────
    {"name": "Rouse's Supermarkets",
     "city": "Mobile", "state": "AL", "type": "chain",
     "zip_code": "36606", "lat": 30.682, "lng": -88.121,
     "address": "2620 Dauphin St"},
    {"name": "Greer's Markets",
     "city": "Mobile", "state": "AL", "type": "independent",
     "zip_code": "36608", "lat": 30.697, "lng": -88.112},
    {"name": "Eastern Shore Meat Market",
     "city": "Spanish Fort", "state": "AL", "type": "specialty",
     "zip_code": "36527", "lat": 30.673, "lng": -87.867,
     "address": "30500 AL-181"},
]
# fmt: on

# Legacy names that should be merged into a canonical brand name.
# Any vendor record with an old_name will be renamed; if the new_name
# already exists, deals are reassigned and the duplicate is deleted.
VENDOR_RENAMES = {
    "Whole Foods Market - Germantown":              "Whole Foods Market",
    "Whole Foods Market - Memphis":                 "Whole Foods Market",
    "The Fresh Market - Germantown":                "The Fresh Market",
    "The Fresh Market - Memphis (Poplar)":          "The Fresh Market",
    "The Fresh Market - Memphis (Union)":           "The Fresh Market",
    "Gordon Food Service (Gordon Restaurant Market)": "Gordon Food Service",
}

CUT_SEED = [
    # Beef
    {"name": "Brisket (whole packer)",             "category": "beef"},
    {"name": "Brisket (flat)",                     "category": "beef"},
    {"name": "Chuck roast",                        "category": "beef"},
    {"name": "Short ribs (bone-in)",               "category": "beef"},
    {"name": "Ribeye steak",                       "category": "beef"},
    {"name": "Skirt steak",                        "category": "beef"},
    {"name": "Tri-tip",                            "category": "beef"},
    {"name": "Ground beef (80/20)",                "category": "beef"},
    {"name": "Ground beef (90/10)",                "category": "beef"},
    {"name": "Sirloin steak",                      "category": "beef"},
    {"name": "New York strip",                     "category": "beef"},
    {"name": "Porterhouse steak",                  "category": "beef"},
    {"name": "T-bone steak",                       "category": "beef"},
    {"name": "Filet mignon",                       "category": "beef"},
    # Pork
    {"name": "Baby back ribs",                     "category": "pork"},
    {"name": "Spare ribs",                         "category": "pork"},
    {"name": "St. Louis-cut ribs",                 "category": "pork"},
    {"name": "Pork shoulder (Boston butt)",        "category": "pork"},
    {"name": "Pork tenderloin",                    "category": "pork"},
    {"name": "Pork chops (bone-in)",               "category": "pork"},
    {"name": "Pork chops (boneless)",              "category": "pork"},
    {"name": "Whole pork loin",                    "category": "pork"},
    {"name": "Bacon (slab)",                       "category": "pork"},
    {"name": "Hot dogs",                           "category": "pork"},
    # Poultry
    {"name": "Whole chicken",                      "category": "poultry"},
    {"name": "Chicken breasts (boneless)",         "category": "poultry"},
    {"name": "Chicken thighs (bone-in, skin-on)",  "category": "poultry"},
    {"name": "Chicken wings",                      "category": "poultry"},
    {"name": "Chicken leg quarters",               "category": "poultry"},
    {"name": "Whole turkey",                       "category": "poultry"},
    {"name": "Turkey breast",                      "category": "poultry"},
    {"name": "Ground turkey",                      "category": "poultry"},
    # Seafood
    {"name": "Catfish (whole)",                    "category": "seafood"},
    {"name": "Catfish (fillet)",                   "category": "seafood"},
    {"name": "Shrimp (16/20 count)",               "category": "seafood"},
    {"name": "Salmon fillet",                      "category": "seafood"},
    {"name": "Tuna steak",                         "category": "seafood"},
]

GEO_FIELDS = {"lat", "lng", "zip_code", "address"}

# Names that are in VENDOR_SEED (after any renames) — used to purge orphan records
_SEED_NAMES = {v["name"] for v in VENDOR_SEED}


async def _apply_renames_and_dedup(db) -> None:
    """
    1. Rename legacy location-specific vendor names to their canonical brand name.
    2. For any canonical name that now has multiple records, keep the one
       with the most associated active deals (or the one with geo data),
       reassign all deals / staged_deals to the keeper, and delete the rest.
    """
    # Step 1 — rename old entries
    for old_name, new_name in VENDOR_RENAMES.items():
        old_doc = await db.vendors.find_one({"name": old_name})
        if not old_doc:
            continue
        new_doc = await db.vendors.find_one({"name": new_name})
        if new_doc:
            # Keeper already exists — reassign and delete old
            await db.deals.update_many(
                {"vendor_id": old_doc["_id"]},
                {"$set": {"vendor_id": new_doc["_id"]}},
            )
            await db.staged_deals.update_many(
                {"store_name": old_name},
                {"$set": {"store_name": new_name}},
            )
            await db.vendors.delete_one({"_id": old_doc["_id"]})
        else:
            # Just rename in place
            await db.vendors.update_one(
                {"_id": old_doc["_id"]},
                {"$set": {"name": new_name}},
            )

    # Step 2 — collapse same-name duplicates (e.g. 6× "Kroger")
    all_vendors = await db.vendors.find(
        {"auto_created": {"$ne": True}}
    ).to_list(5000)

    from collections import defaultdict
    by_name: dict = defaultdict(list)
    for v in all_vendors:
        by_name[v["name"]].append(v)

    for name, dupes in by_name.items():
        if len(dupes) <= 1:
            continue

        # Score each candidate: prefer geo data, then most active deals
        async def _deal_count(v):
            return await db.deals.count_documents({"vendor_id": v["_id"], "active": True})

        scored = []
        for v in dupes:
            has_geo = 1 if (v.get("lat") and v.get("lng")) else 0
            cnt = await _deal_count(v)
            scored.append((has_geo * 1000 + cnt, v))

        scored.sort(key=lambda t: t[0], reverse=True)
        keeper = scored[0][1]
        to_remove = [v for _, v in scored[1:]]

        for old in to_remove:
            await db.deals.update_many(
                {"vendor_id": old["_id"]},
                {"$set": {"vendor_id": keeper["_id"]}},
            )
            await db.staged_deals.update_many(
                {"store_name": old["name"]},
                {"$set": {"store_name": keeper["name"]}},
            )
            await db.vendors.delete_one({"_id": old["_id"]})

    # Step 3 — remove vendor records that are no longer in the seed
    # (and have no active deals — safe to delete orphans)
    remaining = await db.vendors.find(
        {"auto_created": {"$ne": True}}
    ).to_list(5000)
    for v in remaining:
        if v["name"] not in _SEED_NAMES:
            deal_count = await db.deals.count_documents(
                {"vendor_id": v["_id"], "active": True}
            )
            if deal_count == 0:
                await db.vendors.delete_one({"_id": v["_id"]})


async def seed_database():
    db = get_db()
    now = datetime.utcnow()

    # Clean up legacy location-specific names and duplicate per-city chain records
    await _apply_renames_and_dedup(db)

    # Upsert by brand name only — one record per brand
    for v in VENDOR_SEED:
        geo_update = {k: v[k] for k in GEO_FIELDS if k in v}
        await db.vendors.update_one(
            {"name": v["name"]},
            {
                "$setOnInsert": {
                    **{k: val for k, val in v.items() if k not in geo_update},
                    "active": True, "featured": False,
                    "auto_created": False, "created_at": now,
                },
                "$set": {**geo_update, "city": v["city"], "state": v["state"]},
            },
            upsert=True,
        )

    for c in CUT_SEED:
        await db.meat_cuts.update_one(
            {"name": c["name"]},
            {"$setOnInsert": {**c, "active": True, "created_at": now}},
            upsert=True,
        )

    if await db.admin_users.count_documents({}) == 0:
        username = os.getenv("ADMIN_USERNAME", "admin")
        password = os.getenv("ADMIN_PASSWORD", "changeme")
        await db.admin_users.insert_one({
            "username": username,
            "hashed_password": hash_password(password),
            "created_at": now,
        })

    await db.deals.create_index([("verified_date", -1)])
    await db.deals.create_index([("active", 1), ("verified_date", -1)])
    await db.deals.create_index([("vendor_id", 1)])
    await db.deals.create_index([("cut_id", 1)])
