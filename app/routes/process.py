from fastapi import APIRouter, UploadFile, File, Request, HTTPException
from app.models.schemas import ProcessResponse
from app.services.html_parser import parse_application_html
from app.services.image_extractor import extract_images_from_html
from app.services.normalizer import build_process_response
from app.utils.timing import Timer

router = APIRouter()


@router.post("/process", response_model=ProcessResponse)
async def process_application(request: Request, file: UploadFile = File(...)) -> ProcessResponse:
    if not file.filename.lower().endswith(".html"):
        raise HTTPException(status_code=400, detail="Only HTML files are supported.")

    html_bytes = await file.read()
    html_text = html_bytes.decode("windows-1252", errors="ignore")

    with Timer() as timer:
        application = parse_application_html(html_text)
        images = extract_images_from_html(html_text)

        ocr_service = request.app.state.ocr_service
        for image in images:
            image.ocr_text = ""
            if image.file_name:
                ocr_result = ocr_service.extract_text(image.file_name)
                image.ocr_text = ocr_result.ocr_text
                image.ocr_regions = ocr_result.ocr_regions
                image.annotated_src = ocr_result.annotated_src
                image.width = ocr_result.width
                image.height = ocr_result.height

        response = build_process_response(
            application=application,
            images=images,
            timing_ms=timer.elapsed_ms,
        )

    return response