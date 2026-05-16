"""
Fuzzy cut-name matching: maps raw product names (from Kroger, Walmart, etc.)
to our canonical MeatCut list using keyword scoring.
"""
import re
from difflib import SequenceMatcher

# Each entry: canonical name → list of keyword phrases (order matters — more specific first)
CUT_KEYWORDS: dict[str, list[str]] = {
    # Beef
    "Brisket (whole packer)": ["whole packer", "packer brisket", "full packer", "whole brisket"],
    "Brisket (flat)":         ["brisket flat", "flat cut brisket", "flat brisket", "brisket"],
    "Chuck roast":            ["chuck roast", "chuck pot roast"],
    "Short ribs (bone-in)":   ["beef short rib", "short rib", "flanken"],
    "Ribeye steak":           ["ribeye", "rib eye", "rib-eye", "prime ribeye"],
    "Sirloin steak":          ["top sirloin", "sirloin steak", "sirloin tip", "bottom sirloin", "sirloin roast"],
    "New York strip":         ["new york strip", "ny strip", "strip steak", "top loin steak"],
    "Porterhouse steak":      ["porterhouse"],
    "T-bone steak":           ["t-bone", "t bone steak", "tbone"],
    "Filet mignon":           ["filet mignon", "beef tenderloin filet", "tenderloin steak", "beef tenderloin"],
    "Skirt steak":            ["skirt steak", "skirt", "flank steak", "flank"],
    "Tri-tip":                ["tri tip", "tri-tip"],
    "Ground beef (80/20)":    ["80/20 ground beef", "ground beef 80/20", "80% lean ground beef", "lean ground beef 80",
                               "ground beef 80", "85/15 ground beef", "ground beef 85"],
    "Ground beef (90/10)":    ["90/10 ground beef", "ground beef 90/10", "90% lean ground beef", "lean ground beef 90",
                               "93/7 ground beef", "ground beef 93", "extra lean ground beef",
                               "ground sirloin", "lean ground sirloin", "ground chuck",
                               "lean ground beef"],
    # Pork
    "Baby back ribs":               ["baby back rib", "baby-back rib"],
    "Spare ribs":                   ["spare rib", "pork spare rib"],
    "St. Louis-cut ribs":           ["st. louis", "st louis", "stl cut rib"],
    "Pork shoulder (Boston butt)":  ["boston butt", "pork butt", "pork shoulder butt", "pork shoulder roast",
                                     "boneless pork shoulder", "pork shoulder"],
    "Pork tenderloin":              ["pork tenderloin", "pork loin filet"],
    "Pork chops (bone-in)":         ["bone-in pork chop", "pork chop bone in", "pork loin chop", "pork rib chop",
                                     "boneless pork loin chop"],
    "Pork chops (boneless)":        ["boneless pork chop", "pork chop boneless", "boneless pork sirloin chop"],
    "Whole pork loin":              ["whole pork loin", "pork loin roast", "center cut pork loin", "boneless pork loin",
                                     "pork half loin", "pork loin"],
    "Bacon (slab)":                 ["slab bacon", "bacon slab", "whole slab", "sliced bacon", "bacon"],
    "Hot dogs":                     ["hot dog", "beef frank", "beef frankfurter", "skinless frank", "frank",
                                     "pork sausage", "italian sausage", "fresh sausage", "bratwurst", "brat sausage",
                                     "kielbasa", "chorizo sausage"],
    # Poultry
    "Whole chicken":                        ["whole fryer", "whole chicken", "fryer chicken", "roasting chicken"],
    "Chicken breasts (boneless)":           ["boneless chicken breast", "boneless skinless chicken breast",
                                             "chicken breast boneless", "chicken tenderloin", "chicken tender"],
    "Chicken thighs (bone-in, skin-on)":    ["bone-in chicken thigh", "chicken thigh bone", "skin-on chicken thigh",
                                             "chicken thigh"],
    "Chicken wings":                        ["chicken wing", "party wing", "wingette", "drumette"],
    "Chicken leg quarters":                 ["leg quarter", "chicken leg quarter", "chicken drumstick"],
    "Whole turkey":                         ["whole turkey", "fresh turkey"],
    "Turkey breast":                        ["turkey breast"],
    "Ground turkey":                        ["ground turkey"],
    # Seafood
    "Catfish (whole)":      ["whole catfish"],
    "Catfish (fillet)":     ["catfish fillet", "catfish filet", "catfish"],
    "Shrimp (16/20 count)": ["shrimp 16/20", "16/20 shrimp", "16-20 shrimp", "extra large shrimp",
                             "gulf shrimp", "shrimp"],
    "Salmon fillet":        ["salmon fillet", "salmon filet", "atlantic salmon", "sockeye salmon", "salmon",
                             "sole fillet", "dover sole", "cod fillet", "cod loin", "halibut fillet",
                             "tilapia fillet", "tilapia", "flounder fillet", "flounder",
                             "mahi fillet", "mahi-mahi", "fish fillet"],
    "Tuna steak":           ["tuna steak", "tuna filet", "ahi tuna", "yellowfin tuna", "albacore tuna", "tuna"],
}

# Category hints for each canonical cut
CUT_CATEGORIES: dict[str, str] = {
    "Brisket (whole packer)": "beef",    "Brisket (flat)": "beef",
    "Chuck roast": "beef",               "Short ribs (bone-in)": "beef",
    "Ribeye steak": "beef",              "Sirloin steak": "beef",
    "New York strip": "beef",            "Porterhouse steak": "beef",
    "T-bone steak": "beef",
    "Filet mignon": "beef",              "Skirt steak": "beef",
    "Tri-tip": "beef",                   "Ground beef (80/20)": "beef",
    "Ground beef (90/10)": "beef",
    "Baby back ribs": "pork",            "Spare ribs": "pork",
    "St. Louis-cut ribs": "pork",        "Pork shoulder (Boston butt)": "pork",
    "Pork tenderloin": "pork",           "Pork chops (bone-in)": "pork",
    "Pork chops (boneless)": "pork",     "Whole pork loin": "pork",
    "Bacon (slab)": "pork",              "Hot dogs": "pork",
    "Whole chicken": "poultry",          "Chicken breasts (boneless)": "poultry",
    "Chicken thighs (bone-in, skin-on)": "poultry",
    "Chicken wings": "poultry",          "Chicken leg quarters": "poultry",
    "Whole turkey": "poultry",           "Turkey breast": "poultry",
    "Ground turkey": "poultry",
    "Catfish (whole)": "seafood",        "Catfish (fillet)": "seafood",
    "Shrimp (16/20 count)": "seafood",   "Salmon fillet": "seafood",
    "Tuna steak": "seafood",
}

# Broad category keywords — used for pre-filtering unrecognised products
CATEGORY_KEYWORDS = {
    "beef":    ["beef", "brisket", "ribeye", "chuck", "skirt", "tri-tip", "steak", "sirloin",
                "t-bone", "t bone", "porterhouse", "filet mignon", "ground beef", "oxtail"],
    "pork":    ["pork", "spare rib", "baby back", "st. louis", "bacon", "ham", "hot dog", "frank",
                "sausage", "bratwurst"],
    "poultry": ["chicken", "turkey", "poultry", "fryer", "wing", "thigh", "drumstick", "ground turkey"],
    "seafood": ["shrimp", "salmon", "catfish", "tilapia", "tuna", "fish", "seafood", "crab", "lobster",
                "sole", "cod", "halibut", "flounder", "mahi", "trout", "snapper"],
}


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s/]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def match_cut(raw_name: str) -> tuple[str | None, float]:
    """
    Returns (canonical_cut_name, confidence 0.0–1.0) or (None, 0.0).
    Confidence >= 0.5 is considered a solid match.
    """
    norm = _normalize(raw_name)
    best_cut: str | None = None
    best_score: float = 0.0

    for cut_name, keywords in CUT_KEYWORDS.items():
        for i, kw in enumerate(keywords):
            if kw in norm:
                # Higher score for earlier (more specific) keywords
                score = 1.0 - (i * 0.05)
                if score > best_score:
                    best_score = score
                    best_cut = cut_name
                break  # only count best keyword per cut

    # Fallback: sequence similarity against canonical names
    if best_score < 0.4:
        for cut_name in CUT_KEYWORDS:
            ratio = SequenceMatcher(None, norm, _normalize(cut_name)).ratio()
            if ratio > best_score:
                best_score = ratio
                best_cut = cut_name

    if best_score < 0.3:
        return None, 0.0

    return best_cut, round(best_score, 3)


def is_meat_product(raw_name: str) -> bool:
    """Quick pre-filter: is this product likely a meat cut we care about?"""
    norm = _normalize(raw_name)
    for keywords in CATEGORY_KEYWORDS.values():
        if any(kw in norm for kw in keywords):
            return True
    return False


def infer_price_unit(raw_name: str, sold_by: str | None = None) -> str:
    """Infer per_lb / per_unit / per_pack from product name and sold_by hint."""
    if sold_by:
        s = sold_by.lower()
        if "weight" in s or "lb" in s:
            return "per_lb"
        if "unit" in s or "each" in s:
            return "per_unit"

    norm = _normalize(raw_name)
    per_unit_hints = ["whole ", "each", "per unit", "rack", "roast", "leg quarter", "whole chicken", "whole turkey"]
    if any(h in norm for h in per_unit_hints):
        return "per_unit"

    return "per_lb"  # default for meat
