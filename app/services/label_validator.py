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
