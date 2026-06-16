import json

import httpx
from fastapi import APIRouter, HTTPException, Query, Request

from app.models.schemas import ApplicationData, ProcessResponse, ProcessUrlRequest
from app.services.html_parser import parse_application_html
from app.services.image_extractor import extract_ttb_assets_from_remote_html
from app.services.label_rules import evaluate_label
from app.services.label_validator import validate_application_against_ocr
from app.services.normalizer import build_process_response
from app.utils.text_normalization import clean_text
from app.utils.timing import Timer

router = APIRouter()


def clean_application_data(application: ApplicationData) -> ApplicationData:
    for field_name in application.model_fields:
        value = getattr(application, field_name, "")
        if isinstance(value, str):
            setattr(application, field_name, clean_text(value))
    return application


def populate_serial_fields(application: ApplicationData) -> ApplicationData:
    serial_value = "".join(ch for ch in (application.serial_number or "") if ch.isdigit())

    year_part = serial_value[:2]
    number_part = serial_value[2:6]

    application.serial_year_1 = year_part[0] if len(year_part) > 0 else ""
    application.serial_year_2 = year_part[1] if len(year_part) > 1 else ""

    application.serial_number_1 = number_part[0] if len(number_part) > 0 else ""
    application.serial_number_2 = number_part[1] if len(number_part) > 1 else ""
    application.serial_number_3 = number_part[2] if len(number_part) > 2 else ""
    application.serial_number_4 = number_part[3] if len(number_part) > 3 else ""

    application.serial_number = f"{year_part}-{number_part}" if year_part or number_part else ""
    return application


def build_label_rule_results(application: ApplicationData, uploaded_images: list[dict]) -> list[dict]:
    beverage_category = (application.type_of_product or "").strip().lower()
    label_rule_results: list[dict] = []

    for image_result in uploaded_images:
        regions = image_result.get("ocr_regions") or []

        if beverage_category:
            label_rule_results.append(
                {
                    "file_name": image_result.get("file_name", ""),
                    "image_type": image_result.get("image_type", ""),
                    "result": evaluate_label(
                        regions=regions,
                        category=beverage_category,
                        expected_brand_name=application.brand_name or application.fanciful_name or None,
                    ),
                }
            )

        label_rule_results.append(
            {
                "file_name": image_result.get("file_name", ""),
                "image_type": image_result.get("image_type", ""),
                "result": evaluate_label(
                    regions=regions,
                    category="warning",
                ),
            }
        )

    return label_rule_results


@router.post("/process-url", response_model=ProcessResponse)
async def process_application_url(
    payload: ProcessUrlRequest,
    include_images: bool = Query(True),
) -> ProcessResponse:
    source_url = payload.source_url

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=30.0,
            verify=False,
            headers={"User-Agent": "Mozilla/5.0"},
        ) as client:
            response = await client.get(source_url)
            response.raise_for_status()

            html_text = response.text

            with Timer() as timer:
                application = parse_application_html(html_text)
                application = clean_application_data(application)
                application = populate_serial_fields(application)

                images = []
                signature_image = None

                if include_images:
                    signature_src, images = await extract_ttb_assets_from_remote_html(
                        html_text=html_text,
                        base_url=source_url,
                        client=client,
                    )
                    if signature_src:
                        signature_image = signature_src

                if not (application.signature or "").strip():
                    application.signature = "Application was e-filed"

                ocr_payload = [image.model_dump() for image in images]
                validation = validate_application_against_ocr(application, ocr_payload)
                label_rule_results = build_label_rule_results(application, ocr_payload)

                result = build_process_response(
                    application=application,
                    images=images,
                    timing_ms=timer.elapsed_ms,
                )
                result.validation = validation
                result.label_rule_results = label_rule_results
                result.signature_image = signature_image
                return result

    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to fetch application URL: {exc}")


@router.post("/submit")
async def submit_application_form(request: Request):
    form = await request.form()
    ocr_service = request.app.state.ocr_service

    label_images = form.getlist("label_images")
    remote_image_urls_raw = str(form.get("remote_image_urls", "[]"))
    remote_image_urls = json.loads(remote_image_urls_raw) if remote_image_urls_raw else []

    serial_year_1 = str(form.get("serial_year_1", ""))
    serial_year_2 = str(form.get("serial_year_2", ""))
    serial_number_1 = str(form.get("serial_number_1", ""))
    serial_number_2 = str(form.get("serial_number_2", ""))
    serial_number_3 = str(form.get("serial_number_3", ""))
    serial_number_4 = str(form.get("serial_number_4", ""))

    serial_year = f"{serial_year_1}{serial_year_2}".strip()
    serial_suffix = f"{serial_number_1}{serial_number_2}{serial_number_3}{serial_number_4}".strip()
    serial_number = f"{serial_year}-{serial_suffix}" if serial_year or serial_suffix else ""

    application = ApplicationData(
        ttb_id=str(form.get("ttb_id", "")),
        ct=str(form.get("ct", "")),
        or_value=str(form.get("or_value", "")),
        rep_id_no=str(form.get("rep_id_no", "")),
        plant_registry_basic_permit_brewers_no=str(form.get("plant_registry_basic_permit_brewers_no", "")),
        source_of_product=str(form.get("source_of_product", "")),
        serial_number=serial_number,
        serial_year_1=serial_year_1,
        serial_year_2=serial_year_2,
        serial_number_1=serial_number_1,
        serial_number_2=serial_number_2,
        serial_number_3=serial_number_3,
        serial_number_4=serial_number_4,
        type_of_product=str(form.get("type_of_product", "")),
        brand_name=str(form.get("brand_name", "")),
        fanciful_name=str(form.get("fanciful_name", "")),
        name_and_address=str(form.get("name_and_address", "")),
        mailing_address=str(form.get("mailing_address", "")),
        formula=str(form.get("formula", "")),
        grape_varietal=str(form.get("grape_varietal", "")),
        wine_appellation=str(form.get("wine_appellation", "")),
        phone_number=str(form.get("phone_number", "")),
        email_address=str(form.get("email_address", "")),
        fax_number=str(form.get("fax_number", "")),
        type_of_application=str(form.get("type_of_application", "")),
        sale_in_state=str(form.get("sale_in_state", "")),
        bottle_capacity=str(form.get("bottle_capacity", "")),
        resubmission_ttb_id=str(form.get("resubmission_ttb_id", "")),
        container_notes=str(form.get("container_notes", "")),
        date_of_application=str(form.get("date_of_application", "")),
        signature=str(form.get("signature", "")),
        print_name_of_applicant=str(form.get("print_name_of_applicant", "")),
        date_issued=str(form.get("date_issued", "")),
        authorized_signature=str(form.get("authorized_signature", "")),
        qualifications=str(form.get("qualifications", "")),
        expiration_date=str(form.get("expiration_date", "")),
        net_contents=str(form.get("net_contents", "")),
        alcohol_content=str(form.get("alcohol_content", "")),
        wine_vintage_date=str(form.get("wine_vintage_date", "")),
    )

    uploaded_images = []

    for image in label_images:
        if not hasattr(image, "read"):
            continue

        image_bytes = await image.read()
        if not image_bytes:
            continue

        ocr_result = ocr_service.extract_text_from_bytes(
            image_bytes=image_bytes,
            file_name=getattr(image, "filename", None) or "uploaded-image.png",
        )

        uploaded_images.append(ocr_result.model_dump())

    if remote_image_urls:
        base_url = str(request.base_url).rstrip("/")

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=30.0,
            verify=False,
        ) as client:
            for image_url in remote_image_urls:
                full_image_url = f"{base_url}{image_url}" if image_url.startswith("/") else image_url

                try:
                    response = await client.get(full_image_url)
                    response.raise_for_status()
                except Exception:
                    continue

                image_bytes = response.content
                if not image_bytes:
                    continue

                file_name = image_url.rstrip("/").rsplit("/", 1)[-1] or "remote-image.jpg"

                ocr_result = ocr_service.extract_text_from_bytes(
                    image_bytes=image_bytes,
                    file_name=file_name,
                )

                uploaded_images.append(ocr_result.model_dump())

    validation = validate_application_against_ocr(application, uploaded_images)
    label_rule_results = build_label_rule_results(application, uploaded_images)

    return {
        "application": application.model_dump(),
        "label_images": uploaded_images,
        "validation": validation,
        "label_rule_results": label_rule_results,
    }
