from app.models.schemas import ApplicationData, ImageResult, ProcessResponse


def build_process_response(
    application: ApplicationData,
    images: list[ImageResult],
    timing_ms: int,
) -> ProcessResponse:
    return ProcessResponse(
        application=application,
        images=images,
        timing_ms=timing_ms,
        warnings=[],
    )