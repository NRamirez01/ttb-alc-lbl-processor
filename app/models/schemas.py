from pydantic import BaseModel, Field
from typing import List, Optional, Any

class ProcessUrlRequest(BaseModel):
    source_url: str

class ApplicationData(BaseModel):
    ttb_id: str = ""
    ct: str = ""
    or_value: str = ""

    rep_id_no: str = ""

    plant_registry_basic_permit_brewers_no: str = ""
    source_of_product: str = ""

    serial_number: str = ""
    serial_year_1: str = ""
    serial_year_2: str = ""
    serial_number_1: str = ""
    serial_number_2: str = ""
    serial_number_3: str = ""
    serial_number_4: str = ""

    type_of_product: str = ""
    brand_name: str = ""
    fanciful_name: str = ""

    name_and_address: str = ""
    mailing_address: str = ""

    formula: str = ""
    grape_varietal: str = ""
    wine_appellation: str = ""

    phone_number: str = ""
    email_address: str = ""
    fax_number: str = ""

    type_of_application: str = ""
    sale_in_state: str = ""
    bottle_capacity: str = ""
    resubmission_ttb_id: str = ""

    container_notes: str = ""

    date_of_application: str = ""
    signature: str = ""
    print_name_of_applicant: str = ""

    date_issued: str = ""
    authorized_signature: str = ""
    qualifications: str = ""
    expiration_date: str = ""

    net_contents: str = ""
    alcohol_content: str = ""
    wine_vintage_date: str = ""

class OCRRegion(BaseModel):
    label: str
    text: str
    bbox: list[int]
    polygon_points: Optional[list[list[float]]] = None
    score: Optional[float] = None
    order: Optional[int] = None


class ImageResult(BaseModel):
    image_type: str
    file_name: str
    src: str
    ocr_text: str = ""
    ocr_html: Optional[str] = None
    ocr_regions: list[OCRRegion] = Field(default_factory=list)
    annotated_src: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class ProcessResponse(BaseModel):
    application: ApplicationData
    images: list[ImageResult] = Field(default_factory=list)
    timing_ms: int
    warnings: list[str] = Field(default_factory=list)
    validation: dict[str, Any] = Field(default_factory=dict)
    label_rule_results: list[dict[str, Any]] = Field(default_factory=list)
    signature_image: Optional[str] = None