from pydantic import BaseModel, Field
from typing import List, Optional

class ApplicationData(BaseModel):
    ttb_id: str = ""
    plant_registry_basic_permit_brewers_no: str = ""
    source_of_product: str = ""
    serial_number: str = ""
    type_of_product: str = ""
    brand_name: str = ""
    fanciful_name: str = ""
    name_and_address: str = ""
    mailing_address: str = ""
    email_address: str = ""
    grape_varietal: str = ""
    formula: str = ""
    net_contents: str = ""
    alcohol_content: str = ""
    wine_appellation: str = ""
    wine_vintage_date: str = ""
    phone_number: str = ""
    fax_number: str = ""
    date_of_application: str = ""
    # signature: str = ""
    print_name_of_applicant: str = ""
    type_of_application: str = ""

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
    ocr_regions: list[OCRRegion] = Field(default_factory=list)
    annotated_src: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class ProcessResponse(BaseModel):
    application: ApplicationData
    images: list[ImageResult] = Field(default_factory=list)
    timing_ms: int
    warnings: list[str] = Field(default_factory=list)