from typing import Any, Optional
from app.models.schemas import ApplicationData, ImageResult, ProcessResponse
def build_process_response(
    application,
    images,
    timing_ms,
    validation=None,
    label_rule_results=None,
    signature_image=None,
) -> ProcessResponse:
    return ProcessResponse(
        application=application,
        images=images,
        timing_ms=timing_ms,
        warnings=[],
        validation=validation or {},
        label_rule_results=label_rule_results or [],
        signature_image=signature_image,
    )