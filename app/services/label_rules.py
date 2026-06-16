import re
from typing import Any, Dict, List, Optional


ALCOHOL_RE = re.compile(
    r"\b(?:alc\.?\s*)?\d{1,2}(?:\.\d+)?\s*(?:%|percent)\s*(?:alcohol\s*)?(?:by\s*)?(?:vol(?:ume)?\.?)\b"
    r"|\b\d+\s*proof\b",
    re.IGNORECASE,
)

NET_CONTENTS_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:ml|mL|l|L|liters?|litres?|fl\.?\s*oz\.?|oz\.?)\b",
    re.IGNORECASE,
)

WARNING_REQUIRED_SNIPPETS = [
    "government warning",
    "surgeon general",
    "pregnancy",
    "drive a car or operate machinery",
]

WINE_CLASS_TERMS = [
    "table wine",
    "light wine",
    "sparkling wine",
    "carbonated wine",
    "fruit wine",
    "berry wine",
    "citrus wine",
    "vermouth",
    "wine",
]

MALT_CLASS_TERMS = [
    "malt beverage",
    "beer",
    "ale",
    "porter",
    "stout",
    "lager",
    "malt liquor",
]

SPIRITS_CLASS_TERMS = [
    "distilled spirits",
    "vodka",
    "whisky",
    "whiskey",
    "bourbon",
    "rye whisky",
    "rye whiskey",
    "rum",
    "gin",
    "tequila",
    "mezcal",
    "brandy",
    "cordial",
    "liqueur",
]


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip().lower()


def region_text(region: Dict[str, Any]) -> str:
    return region.get("text", "") or ""


def region_group_id(region: Dict[str, Any], index: int) -> str:
    order = region.get("order")
    if order is not None:
        return f"group_{order}"
    return f"group_{index}"


def looks_like_alcohol_content(text: str) -> bool:
    return bool(ALCOHOL_RE.search(text or ""))


def looks_like_net_contents(text: str) -> bool:
    return bool(NET_CONTENTS_RE.search(text or ""))


def looks_like_warning(text: str) -> bool:
    t = _norm(text)
    return "government warning" in t and (
        "surgeon general" in t or "pregnancy" in t or "drive a car or operate machinery" in t
    )


def contains_any(text: str, terms: List[str]) -> bool:
    t = _norm(text)
    return any(term in t for term in terms)


def find_first_region(regions: List[Dict[str, Any]], predicate) -> Optional[str]:
    for idx, region in enumerate(regions):
        text = region_text(region)
        if predicate(text):
            return region_group_id(region, idx)
    return None


def find_region_by_exactish_value(regions: List[Dict[str, Any]], value: str) -> Optional[str]:
    needle = _norm(value)
    if not needle:
        return None

    for idx, region in enumerate(regions):
        hay = _norm(region_text(region))
        if needle and needle in hay:
            return region_group_id(region, idx)
    return None


def collect_all_text(regions: List[Dict[str, Any]]) -> str:
    return "\n".join(region_text(region) for region in regions)


def build_presence(status: bool, region_id: Optional[str] = None) -> Dict[str, Any]:
    return {
        "status": "present" if status else "missing",
        "region_id": region_id,
    }


def evaluate_same_field_of_vision(found: Dict[str, Optional[str]], required: List[str]) -> Dict[str, Any]:
    region_ids = [found.get(name) for name in required]
    ok = all(region_ids) and len(set(region_ids)) == 1
    return {
        "status": "pass" if ok else "fail",
        "required": required,
        "regions": {name: found.get(name) for name in required},
    }


def evaluate_label(
    regions: List[Dict[str, Any]],
    category: str,
    abv: Optional[float] = None,
    expected_brand_name: Optional[str] = None,
) -> Dict[str, Any]:
    category = (category or "").strip().lower()
    all_text = collect_all_text(regions)

    # Prefer an OCR region that actually contains the known brand name.
    brand_region = None
    if expected_brand_name:
        brand_region = find_region_by_exactish_value(regions, expected_brand_name)

    # Fallback MVP heuristic
    if not brand_region:
        brand_region = find_first_region(
            regions,
            lambda t: not looks_like_alcohol_content(t)
            and not looks_like_net_contents(t)
            and len(_norm(t)) > 2
        )

    if category == "distilled_spirits":
        class_region = find_first_region(regions, lambda t: contains_any(t, SPIRITS_CLASS_TERMS))
        alcohol_region = find_first_region(regions, looks_like_alcohol_content)
        name_addr_region = find_first_region(
            regions,
            lambda t: "imported by" in _norm(t)
            or "bottled by" in _norm(t)
            or "distilled by" in _norm(t)
            or "produced by" in _norm(t)
        )
        net_region = find_first_region(regions, looks_like_net_contents)

        found = {
            "brand_name": brand_region,
            "class_type": class_region,
            "alcohol_content": alcohol_region,
        }

        return {
            "category": category,
            "checks": {
                "brand_name": build_presence(bool(brand_region), brand_region),
                "class_type": build_presence(bool(class_region), class_region),
                "alcohol_content": build_presence(bool(alcohol_region), alcohol_region),
                "name_address": build_presence(bool(name_addr_region), name_addr_region),
                "net_contents": build_presence(bool(net_region), net_region),
                "same_field_of_vision": evaluate_same_field_of_vision(
                    found,
                    ["brand_name", "class_type", "alcohol_content"],
                ),
            },
            "combined_ocr_text": all_text,
        }

    if category == "malt_beverages":
        class_region = find_first_region(regions, lambda t: contains_any(t, MALT_CLASS_TERMS))
        alcohol_region = find_first_region(regions, looks_like_alcohol_content)
        name_addr_region = find_first_region(
            regions,
            lambda t: "imported by" in _norm(t)
            or "brewed" in _norm(t)
            or "bottled by" in _norm(t)
            or "packed by" in _norm(t)
        )
        net_region = find_first_region(regions, looks_like_net_contents)

        alcohol_required = False if abv is None else False  # MVP: don't hard-fail when missing

        return {
            "category": category,
            "checks": {
                "brand_name": build_presence(bool(brand_region), brand_region),
                "class_type": build_presence(bool(class_region), class_region),
                "alcohol_content": {
                    "status": "present" if alcohol_region else ("missing" if alcohol_required else "optional_missing"),
                    "region_id": alcohol_region,
                    "required_logic": "mandatory only for certain flavored/ingredient-added products or state-law scenarios",
                },
                "name_address": build_presence(bool(name_addr_region), name_addr_region),
                "net_contents": build_presence(bool(net_region), net_region),
            },
            "combined_ocr_text": all_text,
        }

    if category == "wine":
        class_region = find_first_region(regions, lambda t: contains_any(t, WINE_CLASS_TERMS))
        alcohol_region = find_first_region(regions, looks_like_alcohol_content)
        name_addr_region = find_first_region(
            regions,
            lambda t: "imported by" in _norm(t)
            or "bottled by" in _norm(t)
            or "packed by" in _norm(t)
            or "produced by" in _norm(t)
        )
        net_region = find_first_region(regions, looks_like_net_contents)

        alcohol_required = abv is not None and abv > 14

        return {
            "category": category,
            "checks": {
                "brand_name": build_presence(bool(brand_region), brand_region),
                "class_type": build_presence(bool(class_region), class_region),
                "alcohol_content": {
                    "status": "present" if alcohol_region else ("missing" if alcohol_required else "optional_missing"),
                    "region_id": alcohol_region,
                },
                "name_address": build_presence(bool(name_addr_region), name_addr_region),
                "net_contents": build_presence(bool(net_region), net_region),
            },
            "combined_ocr_text": all_text,
        }

    if category == "warning":
        warning_region = find_first_region(regions, looks_like_warning)
        return {
            "category": category,
            "checks": {
                "government_warning": build_presence(bool(warning_region), warning_region),
            },
            "combined_ocr_text": all_text,
        }

    return {
        "category": category,
        "checks": {},
        "combined_ocr_text": all_text,
    }