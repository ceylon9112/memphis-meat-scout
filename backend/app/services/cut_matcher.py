"""
Cut-name matching: maps raw retail product names to canonical MeatCut entries.

Scoring strategy:
  1.0   exact first keyword hit + category signal in product name
  0.95  first keyword hit (no category signal)
  0.90  second keyword hit + category signal
  0.80  any later keyword hit
  0.50–0.70  sequence-ratio fallback
  0.0   no match

Price sanity bounds (per_lb) are used by the discovery pipeline to flag
obviously wrong prices without blocking publication.
"""
import re
from difflib import SequenceMatcher

# ─── Canonical keyword map ────────────────────────────────────────────────────
# More-specific / exact phrases come first; generic terms last.
CUT_KEYWORDS: dict[str, list[str]] = {
    # ── Beef ──────────────────────────────────────────────────────────────────
    "Brisket (whole packer)": [
        "whole packer", "packer brisket", "full packer", "whole brisket", "brisket",
    ],
    "Brisket (flat)": [
        "brisket flat", "flat cut brisket", "flat brisket",
    ],
    "Chuck roast": [
        "chuck roast", "chuck pot roast", "chuck arm roast", "shoulder arm roast",
        "chuck shoulder", "ranch steak", "chuck steak", "beef chuck",
        "blade roast", "blade steak",
    ],
    "Short ribs (bone-in)": [
        "beef short rib", "short rib", "flanken", "korean cut rib", "beef rib",
        "plate rib", "dinosaur rib",
    ],
    "Ribeye steak": [
        "ribeye", "rib eye", "rib-eye", "prime ribeye", "tomahawk", "cowboy ribeye",
        "cowboy steak", "bone-in ribeye", "boneless ribeye", "rib steak",
    ],
    "Sirloin steak": [
        "top sirloin", "sirloin steak", "sirloin tip", "bottom sirloin",
        "sirloin roast", "flat iron", "flat-iron", "coulotte",
    ],
    "New York strip": [
        "new york strip", "ny strip", "strip steak", "top loin steak",
        "kansas city strip", "shell steak",
    ],
    "Porterhouse steak": [
        "porterhouse",
    ],
    "T-bone steak": [
        "t-bone", "t bone steak", "tbone",
    ],
    "Filet mignon": [
        "filet mignon", "beef tenderloin filet", "tenderloin steak",
        "beef tenderloin", "chateaubriand",
    ],
    "Skirt steak": [
        "skirt steak", "inside skirt", "outside skirt", "flank steak", "flank",
        "hanger steak", "hanging tender",
    ],
    "Tri-tip": [
        "tri tip", "tri-tip", "triangle roast", "triangle steak",
    ],
    "Ground beef (80/20)": [
        "80/20 ground beef", "ground beef 80/20", "80% lean ground beef",
        "ground beef 80", "85/15 ground beef", "ground beef 85",
        "regular ground beef", "ground beef value", "ground beef family",
    ],
    "Ground beef (90/10)": [
        "90/10 ground beef", "ground beef 90/10", "90% lean ground beef",
        "93/7 ground beef", "ground beef 93", "extra lean ground beef",
        "ground sirloin", "lean ground sirloin", "ground chuck",
        "lean ground beef", "ground beef 96",
    ],
    # ── Pork ──────────────────────────────────────────────────────────────────
    "Baby back ribs": [
        "baby back rib", "baby-back rib", "loin back rib",
    ],
    "Spare ribs": [
        "spare rib", "pork spare rib",
    ],
    "St. Louis-cut ribs": [
        "st. louis", "st louis", "stl cut rib", "saint louis rib",
    ],
    "Pork shoulder (Boston butt)": [
        "boston butt", "pork butt", "pork shoulder butt", "pork shoulder roast",
        "boneless pork shoulder", "pork shoulder", "country style rib",
        "country-style rib",
    ],
    "Pork tenderloin": [
        "pork tenderloin", "pork loin filet", "pork loin fillet",
    ],
    "Pork chops (bone-in)": [
        "bone-in pork chop", "pork chop bone in", "pork loin chop",
        "pork rib chop", "center cut pork chop", "pork blade chop",
    ],
    "Pork chops (boneless)": [
        "boneless pork chop", "pork chop boneless", "boneless pork sirloin chop",
        "boneless center cut pork chop",
    ],
    "Whole pork loin": [
        "whole pork loin", "pork loin roast", "center cut pork loin",
        "boneless pork loin", "pork half loin", "pork loin",
    ],
    "Bacon (slab)": [
        "slab bacon", "bacon slab", "whole slab bacon", "thick cut bacon",
        "sliced bacon", "bacon",
    ],
    "Hot dogs": [
        "hot dog", "beef frank", "beef frankfurter", "skinless frank", "frankfurter",
        "smoked sausage", "andouille", "kielbasa", "chorizo sausage",
        "italian sausage", "fresh sausage link", "bratwurst", "brat sausage",
        "summer sausage", "link sausage", "pork sausage link",
    ],
    # ── Poultry ───────────────────────────────────────────────────────────────
    "Whole chicken": [
        "whole fryer", "whole chicken", "fryer chicken", "roasting chicken",
        "whole bird", "air chilled whole chicken",
    ],
    "Chicken breasts (boneless)": [
        "boneless skinless chicken breast", "boneless chicken breast",
        "chicken breast boneless", "chicken tenderloin", "chicken tender",
        "chicken breast fillet", "chicken cutlet", "air chilled chicken breast",
        "thin sliced chicken breast", "chicken breast",
    ],
    "Chicken thighs (bone-in, skin-on)": [
        "bone-in chicken thigh", "chicken thigh bone", "skin-on chicken thigh",
        "bone in skin on chicken thigh", "chicken thigh",
    ],
    "Chicken wings": [
        "chicken wing", "party wing", "wingette", "drumette",
        "split chicken wing",
    ],
    "Chicken leg quarters": [
        "leg quarter", "chicken leg quarter", "chicken drumstick",
        "chicken leg", "drum stick",
    ],
    "Whole turkey": [
        "whole turkey", "fresh turkey", "frozen turkey", "young turkey",
    ],
    "Turkey breast": [
        "turkey breast", "bone-in turkey breast", "boneless turkey breast",
    ],
    "Ground turkey": [
        "ground turkey", "lean ground turkey", "ground turkey breast",
    ],
    # ── Seafood ───────────────────────────────────────────────────────────────
    "Catfish (whole)": [
        "whole catfish", "live catfish",
    ],
    "Catfish (fillet)": [
        "catfish fillet", "catfish filet", "catfish strip", "catfish",
    ],
    "Shrimp (16/20 count)": [
        "shrimp 16/20", "16/20 shrimp", "16-20 shrimp", "extra large shrimp",
        "jumbo shrimp", "gulf shrimp", "wild caught shrimp", "shrimp",
    ],
    "Salmon fillet": [
        "salmon fillet", "salmon filet", "atlantic salmon", "sockeye salmon",
        "king salmon", "coho salmon", "salmon steak", "salmon",
        "cod fillet", "cod loin", "halibut fillet", "halibut steak",
        "tilapia fillet", "tilapia", "flounder fillet", "flounder",
        "mahi fillet", "mahi-mahi", "sole fillet", "dover sole",
        "sea bass", "snapper fillet", "snapper", "trout fillet", "trout",
        "fish fillet",
    ],
    "Tuna steak": [
        "tuna steak", "tuna filet", "ahi tuna", "yellowfin tuna",
        "albacore tuna", "bluefin tuna", "tuna",
    ],
}

# ── Category hints ────────────────────────────────────────────────────────────
CUT_CATEGORIES: dict[str, str] = {
    "Brisket (whole packer)": "beef",    "Brisket (flat)": "beef",
    "Chuck roast": "beef",               "Short ribs (bone-in)": "beef",
    "Ribeye steak": "beef",              "Sirloin steak": "beef",
    "New York strip": "beef",            "Porterhouse steak": "beef",
    "T-bone steak": "beef",              "Filet mignon": "beef",
    "Skirt steak": "beef",               "Tri-tip": "beef",
    "Ground beef (80/20)": "beef",       "Ground beef (90/10)": "beef",
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

# Category signal words — if the raw name contains one, boost confidence
CATEGORY_SIGNALS: dict[str, list[str]] = {
    "beef":    ["beef", "angus", "wagyu", "usda", "prime beef", "choice beef"],
    "pork":    ["pork", "swine", "ham"],
    "poultry": ["chicken", "turkey", "poultry"],
    "seafood": ["salmon", "shrimp", "catfish", "tuna", "fish", "seafood",
                "tilapia", "cod", "halibut", "flounder", "mahi"],
}

# Broad meat detection — pre-filter before scoring
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "beef":    ["beef", "brisket", "ribeye", "chuck", "skirt", "tri-tip", "steak",
                "sirloin", "t-bone", "porterhouse", "filet mignon", "ground beef",
                "oxtail", "tomahawk", "cowboy", "flat iron"],
    "pork":    ["pork", "spare rib", "baby back", "st. louis", "bacon", "ham",
                "hot dog", "frank", "sausage", "bratwurst", "kielbasa", "chorizo",
                "andouille", "country rib"],
    "poultry": ["chicken", "turkey", "poultry", "fryer", "wing", "thigh",
                "drumstick", "ground turkey"],
    "seafood": ["shrimp", "salmon", "catfish", "tilapia", "tuna", "fish", "seafood",
                "crab", "lobster", "sole", "cod", "halibut", "flounder", "mahi",
                "trout", "snapper", "bass"],
}

# Reasonable price-per-lb bounds for sanity checking.
# Per-unit / per-pack items may not conform — caller should check price_unit.
PRICE_BOUNDS: dict[str, tuple[float, float]] = {
    "Brisket (whole packer)":         (2.00,  9.00),
    "Brisket (flat)":                 (3.50, 14.00),
    "Chuck roast":                    (2.50, 11.00),
    "Short ribs (bone-in)":           (3.50, 18.00),
    "Ribeye steak":                   (7.00, 40.00),
    "Sirloin steak":                  (4.00, 28.00),
    "New York strip":                 (7.00, 35.00),
    "Porterhouse steak":              (7.00, 38.00),
    "T-bone steak":                   (6.00, 32.00),
    "Filet mignon":                   (12.00, 60.00),
    "Skirt steak":                    (4.00, 22.00),
    "Tri-tip":                        (4.00, 22.00),
    "Ground beef (80/20)":            (2.50, 10.00),
    "Ground beef (90/10)":            (3.00, 12.00),
    "Baby back ribs":                 (2.50, 13.00),
    "Spare ribs":                     (2.00,  9.00),
    "St. Louis-cut ribs":             (2.50, 11.00),
    "Pork shoulder (Boston butt)":    (1.00,  6.00),
    "Pork tenderloin":                (2.50, 10.00),
    "Pork chops (bone-in)":           (2.00,  9.00),
    "Pork chops (boneless)":          (2.50, 10.00),
    "Whole pork loin":                (1.50,  7.00),
    "Bacon (slab)":                   (2.50, 14.00),
    "Hot dogs":                       (1.00,  9.00),
    "Whole chicken":                  (0.50,  4.00),
    "Chicken breasts (boneless)":     (1.50,  9.00),
    "Chicken thighs (bone-in, skin-on)": (0.75, 5.00),
    "Chicken wings":                  (1.25,  7.00),
    "Chicken leg quarters":           (0.50,  4.00),
    "Whole turkey":                   (0.50,  3.50),
    "Turkey breast":                  (2.00,  9.00),
    "Ground turkey":                  (2.00,  9.00),
    "Catfish (whole)":                (1.50,  8.00),
    "Catfish (fillet)":               (3.00, 14.00),
    "Shrimp (16/20 count)":           (3.00, 22.00),
    "Salmon fillet":                  (5.00, 30.00),
    "Tuna steak":                     (7.00, 35.00),
}


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s/]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _has_category_signal(norm: str, category: str) -> bool:
    return any(sig in norm for sig in CATEGORY_SIGNALS.get(category, []))


def match_cut(raw_name: str) -> tuple[str | None, float]:
    """
    Returns (canonical_cut_name, confidence 0.0–1.0) or (None, 0.0).

    Confidence bands:
      ≥ 0.85  very strong — exact keyword hit with category signal
      ≥ 0.70  strong — keyword hit (was previous auto-approve threshold)
      ≥ 0.50  moderate
      ≥ 0.30  weak — publish but flag for review
       < 0.30  no match
    """
    norm = _normalize(raw_name)
    best_cut: str | None = None
    best_score: float = 0.0

    for cut_name, keywords in CUT_KEYWORDS.items():
        cat = CUT_CATEGORIES.get(cut_name, "")
        has_signal = _has_category_signal(norm, cat)

        for i, kw in enumerate(keywords):
            if kw not in norm:
                continue

            # Specificity bonus: first keywords are more precise
            specificity = max(0.0, 1.0 - i * 0.04)

            # Category signal boosts confidence
            signal_bonus = 0.08 if has_signal else 0.0

            score = min(1.0, specificity + signal_bonus)

            if score > best_score:
                best_score = score
                best_cut = cut_name
            break  # only best keyword per cut

    # Sequence-ratio fallback when keyword score is weak
    if best_score < 0.45:
        for cut_name in CUT_KEYWORDS:
            ratio = SequenceMatcher(None, norm, _normalize(cut_name)).ratio()
            adjusted = ratio * 0.75          # cap fallback scores below keyword hits
            if adjusted > best_score:
                best_score = adjusted
                best_cut = cut_name

    if best_score < 0.25:
        return None, 0.0

    return best_cut, round(best_score, 3)


def is_meat_product(raw_name: str) -> bool:
    """Quick pre-filter: does this product name contain any meat keyword?"""
    norm = _normalize(raw_name)
    return any(
        kw in norm
        for keywords in CATEGORY_KEYWORDS.values()
        for kw in keywords
    )


def is_price_sane(cut_name: str, price: float, price_unit: str = "per_lb") -> bool:
    """
    Return False if the price looks like a scraping error.
    Only applied to per-lb prices (per-unit packs vary too much).
    """
    if price_unit != "per_lb":
        return True
    bounds = PRICE_BOUNDS.get(cut_name)
    if not bounds:
        return True
    lo, hi = bounds
    return lo <= price <= hi


def infer_price_unit(raw_name: str, sold_by: str | None = None) -> str:
    """Infer per_lb / per_unit / per_pack from product name and sold-by hint."""
    if sold_by:
        s = sold_by.lower()
        if "weight" in s or "lb" in s:
            return "per_lb"
        if "unit" in s or "each" in s:
            return "per_unit"

    norm = _normalize(raw_name)
    per_unit_hints = [
        "whole ", "each", "per unit", "rack", "leg quarter",
        "whole chicken", "whole turkey", "whole fryer",
    ]
    if any(h in norm for h in per_unit_hints):
        return "per_unit"

    return "per_lb"
