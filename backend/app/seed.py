from datetime import datetime
from bson import ObjectId
from .database import get_db
from .services.auth import hash_password
import os


# fmt: off
VENDOR_SEED = [
    # ── Memphis / Germantown area ────────────────────────────────────────────
    {"name": "Ramon's Meat Market",
     "city": "Memphis", "state": "TN", "type": "independent",
     "zip_code": "38116", "lat": 35.059, "lng": -90.010,
     "address": "4191 Elvis Presley Blvd"},
    {"name": "Southern Meat Market",
     "city": "Memphis", "state": "TN", "type": "independent",
     "zip_code": "38104", "lat": 35.145, "lng": -90.038},
    {"name": "Fayette Packing",
     "city": "Somerville", "state": "TN", "type": "specialty",
     "zip_code": "38068", "lat": 35.246, "lng": -89.358},
    {"name": "Gordin's",
     "city": "Memphis", "state": "TN", "type": "independent",
     "zip_code": "38104", "lat": 35.145, "lng": -90.040,
     "address": "1161 Union Ave"},
    {"name": "Gordon Food Service (Gordon Restaurant Market)",
     "city": "Memphis", "state": "TN", "type": "wholesale",
     "zip_code": "38116", "lat": 35.062, "lng": -90.028},
    {"name": "Kroger",
     "city": "Memphis", "state": "TN", "type": "chain",
     "zip_code": "38118", "lat": 35.072, "lng": -89.940},
    {"name": "ALDI",
     "city": "Memphis", "state": "TN", "type": "chain",
     "zip_code": "38115", "lat": 35.097, "lng": -89.895},
    {"name": "Walmart",
     "city": "Memphis", "state": "TN", "type": "chain",
     "zip_code": "38128", "lat": 35.226, "lng": -89.946},
    {"name": "Sprouts Farmers Market",
     "city": "Memphis", "state": "TN", "type": "chain",
     "zip_code": "38120", "lat": 35.120, "lng": -89.853},
    {"name": "Market Place",
     "city": "Memphis", "state": "TN", "type": "chain",
     "zip_code": "38103", "lat": 35.149, "lng": -90.048},
    {"name": "Superlo Foods",
     "city": "Memphis", "state": "TN", "type": "chain",
     "zip_code": "38116", "lat": 35.065, "lng": -90.003},
    {"name": "Gene Stimson Big Star",
     "city": "Memphis", "state": "TN", "type": "chain",
     "zip_code": "38118", "lat": 35.080, "lng": -89.930},
    {"name": "Restaurant Depot",
     "city": "Memphis", "state": "TN", "type": "wholesale",
     "zip_code": "38103", "lat": 35.151, "lng": -90.046},
    {"name": "Costco",
     "city": "Memphis", "state": "TN", "type": "chain",
     "zip_code": "38138", "lat": 35.087, "lng": -89.791},
    {"name": "Target",
     "city": "Memphis", "state": "TN", "type": "chain",
     "zip_code": "38119", "lat": 35.094, "lng": -89.849},
    {"name": "Trader Joe's",
     "city": "Germantown", "state": "TN", "type": "chain",
     "zip_code": "38138", "lat": 35.088, "lng": -89.803},
    {"name": "Whole Foods Market - Germantown",
     "city": "Germantown", "state": "TN", "type": "chain",
     "zip_code": "38138", "lat": 35.089, "lng": -89.805},
    {"name": "Whole Foods Market - Memphis",
     "city": "Memphis", "state": "TN", "type": "chain",
     "zip_code": "38120", "lat": 35.120, "lng": -89.853},
    {"name": "The Fresh Market - Germantown",
     "city": "Germantown", "state": "TN", "type": "chain",
     "zip_code": "38138", "lat": 35.087, "lng": -89.800},
    {"name": "The Fresh Market - Memphis (Poplar)",
     "city": "Memphis", "state": "TN", "type": "chain",
     "zip_code": "38117", "lat": 35.106, "lng": -89.851},
    {"name": "The Fresh Market - Memphis (Union)",
     "city": "Memphis", "state": "TN", "type": "chain",
     "zip_code": "38104", "lat": 35.141, "lng": -89.987},

    # Piggly Wiggly — strong Memphis/Mid-South presence
    {"name": "Piggly Wiggly",
     "city": "Memphis", "state": "TN", "type": "chain",
     "zip_code": "38106", "lat": 35.103, "lng": -90.044},
    {"name": "Piggly Wiggly",
     "city": "Jackson", "state": "MS", "type": "chain",
     "zip_code": "39204", "lat": 32.293, "lng": -90.216},

    # Food Lion — Southeast / Appalachian markets
    {"name": "Food Lion",
     "city": "Knoxville", "state": "TN", "type": "chain",
     "zip_code": "37917", "lat": 35.990, "lng": -83.940},
    {"name": "Food Lion",
     "city": "Birmingham", "state": "AL", "type": "chain",
     "zip_code": "35206", "lat": 33.540, "lng": -86.741},
    {"name": "Food Lion",
     "city": "Nashville", "state": "TN", "type": "chain",
     "zip_code": "37210", "lat": 36.143, "lng": -86.749},

    # ── Nashville, TN ────────────────────────────────────────────────────────
    {"name": "Kroger",
     "city": "Nashville", "state": "TN", "type": "chain",
     "zip_code": "37203", "lat": 36.155, "lng": -86.793},
    {"name": "ALDI",
     "city": "Nashville", "state": "TN", "type": "chain",
     "zip_code": "37211", "lat": 36.088, "lng": -86.732},
    {"name": "Walmart",
     "city": "Nashville", "state": "TN", "type": "chain",
     "zip_code": "37207", "lat": 36.211, "lng": -86.766},
    {"name": "Publix",
     "city": "Nashville", "state": "TN", "type": "chain",
     "zip_code": "37215", "lat": 36.100, "lng": -86.835},
    {"name": "Whole Foods Market",
     "city": "Nashville", "state": "TN", "type": "chain",
     "zip_code": "37212", "lat": 36.143, "lng": -86.802},
    {"name": "Trader Joe's",
     "city": "Nashville", "state": "TN", "type": "chain",
     "zip_code": "37215", "lat": 36.099, "lng": -86.837},
    {"name": "The Fresh Market",
     "city": "Nashville", "state": "TN", "type": "chain",
     "zip_code": "37215", "lat": 36.100, "lng": -86.833},
    {"name": "Costco",
     "city": "Nashville", "state": "TN", "type": "chain",
     "zip_code": "37086", "lat": 36.068, "lng": -86.658},
    {"name": "Sprouts Farmers Market",
     "city": "Nashville", "state": "TN", "type": "chain",
     "zip_code": "37215", "lat": 36.101, "lng": -86.830},

    # ── Birmingham, AL ───────────────────────────────────────────────────────
    {"name": "Kroger",
     "city": "Birmingham", "state": "AL", "type": "chain",
     "zip_code": "35205", "lat": 33.499, "lng": -86.817},
    {"name": "ALDI",
     "city": "Birmingham", "state": "AL", "type": "chain",
     "zip_code": "35210", "lat": 33.534, "lng": -86.716},
    {"name": "Walmart",
     "city": "Birmingham", "state": "AL", "type": "chain",
     "zip_code": "35215", "lat": 33.622, "lng": -86.745},
    {"name": "Publix",
     "city": "Birmingham", "state": "AL", "type": "chain",
     "zip_code": "35223", "lat": 33.492, "lng": -86.800},
    {"name": "Whole Foods Market",
     "city": "Birmingham", "state": "AL", "type": "chain",
     "zip_code": "35223", "lat": 33.492, "lng": -86.799},
    {"name": "The Fresh Market",
     "city": "Birmingham", "state": "AL", "type": "chain",
     "zip_code": "35223", "lat": 33.493, "lng": -86.799},
    {"name": "Costco",
     "city": "Birmingham", "state": "AL", "type": "chain",
     "zip_code": "35244", "lat": 33.377, "lng": -86.760},
    {"name": "Western Supermarkets",
     "city": "Birmingham", "state": "AL", "type": "independent",
     "zip_code": "35209", "lat": 33.479, "lng": -86.818},

    # ── Little Rock, AR ──────────────────────────────────────────────────────
    {"name": "Kroger",
     "city": "Little Rock", "state": "AR", "type": "chain",
     "zip_code": "72205", "lat": 34.739, "lng": -92.364},
    {"name": "ALDI",
     "city": "Little Rock", "state": "AR", "type": "chain",
     "zip_code": "72211", "lat": 34.756, "lng": -92.436},
    {"name": "Walmart",
     "city": "Little Rock", "state": "AR", "type": "chain",
     "zip_code": "72209", "lat": 34.683, "lng": -92.372},
    {"name": "Natural Grocers",
     "city": "Little Rock", "state": "AR", "type": "chain",
     "zip_code": "72205", "lat": 34.739, "lng": -92.361},
    {"name": "Whole Foods Market",
     "city": "Little Rock", "state": "AR", "type": "chain",
     "zip_code": "72205", "lat": 34.741, "lng": -92.368},

    # ── Jackson, MS ─────────────────────────────────────────────────────────
    {"name": "Kroger",
     "city": "Jackson", "state": "MS", "type": "chain",
     "zip_code": "39211", "lat": 32.349, "lng": -90.143},
    {"name": "Walmart",
     "city": "Jackson", "state": "MS", "type": "chain",
     "zip_code": "39212", "lat": 32.276, "lng": -90.197},
    {"name": "Winn-Dixie",
     "city": "Jackson", "state": "MS", "type": "chain",
     "zip_code": "39204", "lat": 32.295, "lng": -90.225},
    {"name": "ALDI",
     "city": "Jackson", "state": "MS", "type": "chain",
     "zip_code": "39211", "lat": 32.347, "lng": -90.141},

    # ── Knoxville, TN ───────────────────────────────────────────────────────
    {"name": "Kroger",
     "city": "Knoxville", "state": "TN", "type": "chain",
     "zip_code": "37919", "lat": 35.928, "lng": -83.994},
    {"name": "ALDI",
     "city": "Knoxville", "state": "TN", "type": "chain",
     "zip_code": "37922", "lat": 35.924, "lng": -84.103},
    {"name": "Walmart",
     "city": "Knoxville", "state": "TN", "type": "chain",
     "zip_code": "37912", "lat": 36.021, "lng": -84.003},
    {"name": "Publix",
     "city": "Knoxville", "state": "TN", "type": "chain",
     "zip_code": "37919", "lat": 35.931, "lng": -84.001},
    {"name": "The Fresh Market",
     "city": "Knoxville", "state": "TN", "type": "chain",
     "zip_code": "37919", "lat": 35.929, "lng": -83.997},
    {"name": "Trader Joe's",
     "city": "Knoxville", "state": "TN", "type": "chain",
     "zip_code": "37919", "lat": 35.929, "lng": -84.003},
    {"name": "Food City",
     "city": "Knoxville", "state": "TN", "type": "chain",
     "zip_code": "37917", "lat": 35.988, "lng": -83.937},
    {"name": "Costco",
     "city": "Knoxville", "state": "TN", "type": "chain",
     "zip_code": "37922", "lat": 35.925, "lng": -84.100},
]
# fmt: on

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

# Geo fields that should be updated even if the vendor already exists
GEO_FIELDS = {"lat", "lng", "zip_code", "address"}


async def seed_database():
    db = get_db()
    now = datetime.utcnow()

    for v in VENDOR_SEED:
        geo_update = {k: v[k] for k in GEO_FIELDS if k in v}
        await db.vendors.update_one(
            {"name": v["name"]},
            {
                "$setOnInsert": {**{k: val for k, val in v.items() if k not in geo_update},
                                 "active": True, "featured": False, "created_at": now},
                "$set": geo_update,
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
