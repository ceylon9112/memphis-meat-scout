from datetime import datetime
from bson import ObjectId
from .database import get_db
from .services.auth import hash_password
import os


VENDOR_SEED = [
    # Local independents
    {"name": "Ramon's Meat Market",                           "city": "Memphis",    "state": "TN", "type": "independent"},
    {"name": "Southern Meat Market",                          "city": "Memphis",    "state": "TN", "type": "independent"},
    {"name": "Fayette Packing",                               "city": "Somerville", "state": "TN", "type": "specialty"},
    {"name": "Gordin's",                                      "city": "Memphis",    "state": "TN", "type": "independent"},
    {"name": "Gordon Food Service (Gordon Restaurant Market)", "city": "Memphis",   "state": "TN", "type": "wholesale"},
    # Chain grocery — Memphis locations
    {"name": "Kroger",                     "city": "Memphis", "state": "TN", "type": "chain"},
    {"name": "ALDI",                       "city": "Memphis", "state": "TN", "type": "chain"},
    {"name": "Walmart",                    "city": "Memphis", "state": "TN", "type": "chain"},
    {"name": "Sprouts Farmers Market",     "city": "Memphis", "state": "TN", "type": "chain"},
    {"name": "Market Place",               "city": "Memphis", "state": "TN", "type": "chain"},
    {"name": "Superlo Foods",              "city": "Memphis", "state": "TN", "type": "chain"},
    {"name": "Gene Stimson Big Star",      "city": "Memphis", "state": "TN", "type": "chain"},
    {"name": "Restaurant Depot",           "city": "Memphis", "state": "TN", "type": "wholesale"},
    {"name": "Costco",                     "city": "Memphis",    "state": "TN", "type": "chain"},
    {"name": "Target",                     "city": "Memphis",    "state": "TN", "type": "chain"},
    {"name": "Trader Joe's",               "city": "Germantown", "state": "TN", "type": "chain"},
    {"name": "Whole Foods Market - Germantown", "city": "Germantown", "state": "TN", "type": "chain"},
    {"name": "Whole Foods Market - Memphis",    "city": "Memphis",    "state": "TN", "type": "chain"},
    {"name": "The Fresh Market - Germantown",   "city": "Germantown", "state": "TN", "type": "chain"},
    {"name": "The Fresh Market - Memphis (Poplar)", "city": "Memphis", "state": "TN", "type": "chain"},
    {"name": "The Fresh Market - Memphis (Union)", "city": "Memphis",  "state": "TN", "type": "chain"},
]

CUT_SEED = [
    # Beef
    {"name": "Brisket (whole packer)",    "category": "beef"},
    {"name": "Brisket (flat)",            "category": "beef"},
    {"name": "Chuck roast",               "category": "beef"},
    {"name": "Short ribs (bone-in)",      "category": "beef"},
    {"name": "Ribeye steak",              "category": "beef"},
    {"name": "Skirt steak",               "category": "beef"},
    {"name": "Tri-tip",                   "category": "beef"},
    {"name": "Ground beef (80/20)",       "category": "beef"},
    {"name": "Ground beef (90/10)",       "category": "beef"},
    {"name": "Sirloin steak",             "category": "beef"},
    {"name": "New York strip",            "category": "beef"},
    {"name": "Porterhouse steak",         "category": "beef"},
    {"name": "T-bone steak",              "category": "beef"},
    {"name": "Filet mignon",              "category": "beef"},
    # Pork
    {"name": "Baby back ribs",            "category": "pork"},
    {"name": "Spare ribs",                "category": "pork"},
    {"name": "St. Louis-cut ribs",        "category": "pork"},
    {"name": "Pork shoulder (Boston butt)", "category": "pork"},
    {"name": "Pork tenderloin",           "category": "pork"},
    {"name": "Pork chops (bone-in)",      "category": "pork"},
    {"name": "Pork chops (boneless)",     "category": "pork"},
    {"name": "Whole pork loin",           "category": "pork"},
    {"name": "Bacon (slab)",              "category": "pork"},
    {"name": "Hot dogs",                  "category": "pork"},
    # Poultry
    {"name": "Whole chicken",             "category": "poultry"},
    {"name": "Chicken breasts (boneless)", "category": "poultry"},
    {"name": "Chicken thighs (bone-in, skin-on)", "category": "poultry"},
    {"name": "Chicken wings",             "category": "poultry"},
    {"name": "Chicken leg quarters",      "category": "poultry"},
    {"name": "Whole turkey",              "category": "poultry"},
    {"name": "Turkey breast",             "category": "poultry"},
    {"name": "Ground turkey",             "category": "poultry"},
    # Seafood
    {"name": "Catfish (whole)",           "category": "seafood"},
    {"name": "Catfish (fillet)",          "category": "seafood"},
    {"name": "Shrimp (16/20 count)",      "category": "seafood"},
    {"name": "Salmon fillet",             "category": "seafood"},
    {"name": "Tuna steak",                "category": "seafood"},
]


async def seed_database():
    db = get_db()
    now = datetime.utcnow()

    # Vendors — upsert by name so new chain vendors are added on restart
    for v in VENDOR_SEED:
        await db.vendors.update_one(
            {"name": v["name"]},
            {"$setOnInsert": {**v, "active": True, "created_at": now}},
            upsert=True,
        )

    # Cuts — upsert by name
    for c in CUT_SEED:
        await db.meat_cuts.update_one(
            {"name": c["name"]},
            {"$setOnInsert": {**c, "active": True, "created_at": now}},
            upsert=True,
        )

    # Admin user
    if await db.admin_users.count_documents({}) == 0:
        username = os.getenv("ADMIN_USERNAME", "admin")
        password = os.getenv("ADMIN_PASSWORD", "changeme")
        await db.admin_users.insert_one({
            "username": username,
            "hashed_password": hash_password(password),
            "created_at": now,
        })

    # Indexes
    await db.deals.create_index([("verified_date", -1)])
    await db.deals.create_index([("active", 1), ("verified_date", -1)])
    await db.deals.create_index([("vendor_id", 1)])
    await db.deals.create_index([("cut_id", 1)])
