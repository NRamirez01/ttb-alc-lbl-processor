import re
from typing import Any

from app.models.schemas import ApplicationData


def normalize_for_match(value: str) -> str:
    value = (value or "").upper()
    value = re.sub(r"[^A-Z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def contains_any(haystack: str, values: list[str]) -> tuple[bool, str]:
    normalized_haystack = normalize_for_match(haystack)
    for value in values:
        if not value:
            continue
        normalized_value = normalize_for_match(value)
        if normalized_value and normalized_value in normalized_haystack:
            return True, value
    return False, ""


def compact_lines(value: str) -> list[str]:
    if not value:
        return []

    lines = [line.strip() for line in value.splitlines() if line.strip()]
    compact = " ".join(lines).strip()

    variants: list[str] = []
    variants.extend(lines)
    if compact:
        variants.append(compact)

    seen = set()
    deduped: list[str] = []
    for item in variants:
        key = normalize_for_match(item)
        if key and key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped


def build_name_address_variants(name_and_address: str) -> list[str]:
    if not name_and_address:
        return []

    raw_lines = [line.strip() for line in name_and_address.splitlines() if line.strip()]
    compact = " ".join(raw_lines).strip()

    variants: list[str] = []

    if compact:
        variants.append(compact)

    if raw_lines:
        if len(raw_lines) >= 2:
            variants.append(" ".join(raw_lines[:2]))
        if len(raw_lines) >= 3:
            variants.append(" ".join(raw_lines[:3]))

    tokens = [token.strip(",") for token in re.split(r"\s+", compact) if token.strip(",")]

    meaningful_tokens = [
        token for token in tokens
        if len(normalize_for_match(token)) >= 4
        and token.upper() not in {"INC", "LLC", "LTD", "CO", "CORP", "VA", "PA", "MI", "NY", "CA"}
    ]

    if len(meaningful_tokens) >= 2:
        variants.append(" ".join(meaningful_tokens[:2]))
    if len(meaningful_tokens) >= 3:
        variants.append(" ".join(meaningful_tokens[:3]))
    if len(meaningful_tokens) >= 4:
        variants.append(" ".join(meaningful_tokens[:4]))

    seen = set()
    deduped: list[str] = []
    for item in variants:
        key = normalize_for_match(item)
        if key and len(key) >= 8 and key not in seen:
            seen.add(key)
            deduped.append(item)

    return deduped


def build_product_type_variants(type_of_product: str) -> list[str]:
    normalized = normalize_for_match(type_of_product)

    if normalized == "WINE":
        return [
            "WINE",
            "RED WINE",
            "WHITE WINE",
            "ROSE",
            "TABLE WINE",
            "WHITE TABLE WINE",
            "RED TABLE WINE",
        ]

    if "DISTILLED" in normalized:
        return [
            "DISTILLED SPIRITS",
            "WHISKEY",
            "WHISKY",
            "VODKA",
            "GIN",
            "RUM",
            "TEQUILA",
            "BRANDY",
            "LIQUEUR",
            "CORDIAL",
        ]

    if "MALT" in normalized:
        return [
            "MALT BEVERAGE",
            "MALT BEVERAGES",
            "BEER",
            "ALE",
            "LAGER",
            "PORTER",
            "STOUT",
            "PILSNER",
        ]

    return [type_of_product] if type_of_product else []


def build_net_contents_variants(net_contents: str) -> list[str]:
    if not net_contents:
        return []

    raw = net_contents.strip()
    normalized = normalize_for_match(raw)

    variants = [raw]

    if "ML" in normalized:
        digits = re.sub(r"[^0-9.]", "", raw)
        if digits:
            variants.extend([f"{digits} ML", f"{digits}ML"])

    if "L" in normalized and "ML" not in normalized:
        digits = re.sub(r"[^0-9.]", "", raw)
        if digits:
            variants.extend([f"{digits} L", f"{digits}L"])

    if "OZ" in normalized:
        digits = re.sub(r"[^0-9.]", "", raw)
        if digits:
            variants.extend(
                [
                    f"{digits} OZ",
                    f"{digits} FL OZ",
                    f"{digits} FL. OZ.",
                    f"{digits}OZ",
                ]
            )

    seen = set()
    deduped: list[str] = []
    for item in variants:
        key = normalize_for_match(item)
        if key and key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped


def make_check(
    field: str,
    expected: str,
    found: str,
    status: str,
    message: str,
) -> dict[str, Any]:
    return {
        "field": field,
        "expected": expected,
        "found": found,
        "status": status,
        "message": message,
    }


def find_alcohol_content_in_ocr(ocr_text: str) -> str:
    patterns = [
        r"\b\d+(?:\.\d+)?\s*%\s*ALC\.?\s*BY\s*VOL\.?\b",
        r"\bALC\.?\s*\d+(?:\.\d+)?\s*%\s*BY\s*VOL\.?\b",
        r"\b\d+(?:\.\d+)?\s*%\s*BY\s*VOL\.?\b",
        r"\b\d+\s*PROOF\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, ocr_text, re.IGNORECASE)
        if match:
            return match.group(0)

    return ""


def validate_application_against_ocr(
    application: ApplicationData,
    ocr_results: list[dict[str, Any]],
) -> dict[str, Any]:
    combined_ocr_text = "\n".join((item.get("ocr_text") or "") for item in ocr_results)
    normalized_ocr = normalize_for_match(combined_ocr_text)

    checks: list[dict[str, Any]] = []

    def add_presence_check(
        field: str,
        expected: str,
        candidates: list[str],
        required_in_application: bool = False,
        severity: str = "warning",
    ) -> None:
        if required_in_application and not (expected or "").strip():
            checks.append(
                make_check(
                    field=field,
                    expected=expected,
                    found="",
                    status="missing",
                    message=f"Application field '{field}' is empty.",
                )
            )
            return

        usable_candidates = [candidate for candidate in candidates if candidate and candidate.strip()]
        if not usable_candidates:
            checks.append(
                make_check(
                    field=field,
                    expected=expected,
                    found="",
                    status="not_checked",
                    message=f"No candidate values available to validate '{field}'.",
                )
            )
            return

        found, matched_value = contains_any(normalized_ocr, usable_candidates)

        if found:
            checks.append(
                make_check(
                    field=field,
                    expected=expected,
                    found=matched_value,
                    status="match",
                    message=f"{field} found in OCR text.",
                )
            )
        else:
            fallback_status = "mismatch"
            if severity == "info":
                fallback_status = "not_checked"
            elif severity == "fail":
                fallback_status = "fail"

            checks.append(
                make_check(
                    field=field,
                    expected=expected,
                    found="",
                    status=fallback_status,
                    message=f"{field} not found in OCR text.",
                )
            )

    add_presence_check(
        field="brand_name",
        expected=application.brand_name or "",
        candidates=[application.brand_name or "", application.fanciful_name or ""],
        required_in_application=True,
    )

    add_presence_check(
        field="class_type_designation",
        expected=application.type_of_product or "",
        candidates=build_product_type_variants(application.type_of_product or ""),
    )

    alcohol_found = find_alcohol_content_in_ocr(combined_ocr_text)
    checks.append(
        make_check(
            field="alcohol_content_present",
            expected="Alcohol content statement present on label",
            found=alcohol_found,
            status="match" if alcohol_found else "mismatch",
            message="Alcohol content statement found on label."
            if alcohol_found
            else "Alcohol content statement not found on label.",
        )
    )

    add_presence_check(
        field="net_contents",
        expected=application.net_contents or "",
        candidates=build_net_contents_variants(application.net_contents or ""),
    )

    add_presence_check(
        field="name_and_address",
        expected=application.name_and_address or "",
        candidates=build_name_address_variants(application.name_and_address or ""),
    )

    applicant_variants = compact_lines(application.print_name_of_applicant or "")
    add_presence_check(
        field="print_name_of_applicant",
        expected=application.print_name_of_applicant or "",
        candidates=applicant_variants,
        severity="info",
    )

    warning_match = re.search(
        r"GOVERNMENT WARNING:.*?SURGEON GENERAL.*?(PREGNANCY).*?(DRIVE A CAR OR OPERATE MACHINERY).*?(HEALTH PROBLEMS)",
        combined_ocr_text,
        re.DOTALL,
    )

    uppercase_warning_match = re.search(
        r"GOVERNMENT WARNING:.*?SURGEON GENERAL.*?(PREGNANCY).*?(DRIVE A CAR OR OPERATE MACHINERY).*?(HEALTH PROBLEMS)",
        combined_ocr_text.upper(),
        re.DOTALL,
    )

    if warning_match:
        checks.append(
            make_check(
                field="health_warning_statement",
                expected="Government warning statement present and uppercase",
                found=warning_match.group(0),
                status="match",
                message="Government warning statement found in uppercase.",
            )
        )
    elif uppercase_warning_match:
        checks.append(
            make_check(
                field="health_warning_statement",
                expected="Government warning statement present and uppercase",
                found=uppercase_warning_match.group(0),
                status="mismatch",
                message="Government warning statement found, but not fully uppercase in OCR text.",
            )
        )
    else:
        checks.append(
            make_check(
                field="health_warning_statement",
                expected="Government warning statement present and uppercase",
                found="",
                status="mismatch",
                message="Government warning statement not found.",
            )
        )

    if (application.source_of_product or "").strip().lower() == "imported":
        origin_candidates = [
            "PRODUCT OF",
            "PRODUCED IN",
            "COUNTRY OF ORIGIN",
            "IMPORTED BY",
            "IMPORTED FOR",
        ]
        found_origin, matched_origin = contains_any(normalized_ocr, origin_candidates)
        checks.append(
            make_check(
                field="country_of_origin",
                expected="Imported labels should show origin/import information",
                found=matched_origin,
                status="match" if found_origin else "mismatch",
                message="Import/origin information found."
                if found_origin
                else "Import/origin information not found.",
            )
        )

    if not ocr_results:
        overall_status = "fail"
    elif any(check["status"] == "fail" for check in checks):
        overall_status = "fail"
    elif any(check["status"] == "mismatch" for check in checks):
        overall_status = "warning"
    else:
        overall_status = "pass"

    return {
        "overall_status": overall_status,
        "checks": checks,
        "combined_ocr_text": combined_ocr_text,
    }