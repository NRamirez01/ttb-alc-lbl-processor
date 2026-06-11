from bs4 import BeautifulSoup
from app.models.schemas import ImageResult

import re
from urllib.parse import unquote




def normalize_image_src(src: str) -> str:
    if not src:
        return ""

    src = unquote(src.strip())

    filename_match = re.search(r"[@?&]filename=([^&]+)", src, flags=re.IGNORECASE)

    if filename_match:
        return filename_match.group(1).strip()

    base = src.split("@", 1)[0].strip()
    base = base.rstrip("/")

    if "/" in base:
        base = base.rsplit("/", 1)[-1]

    base = re.sub(r"\.do$", ".jpg", base, flags=re.IGNORECASE)

    return base


def extract_images_from_html(html_text: str) -> list[ImageResult]:
    soup = BeautifulSoup(html_text, "lxml")
    results: list[ImageResult] = []

    for img in soup.find_all("img"):
        src = img.get("src", "")
        alt = img.get("alt", "").lower()

        image_type = "unknown"
        if "signature" in alt:
            image_type = "signature"
        elif "brand" in alt or "front" in alt:
            image_type = "front_label"
        elif "back" in alt:
            image_type = "back_label"

        results.append(
            ImageResult(
                image_type=image_type,
                file_name = r"C:\Users\nrami\Desktop\Code\ttb-alc-lbl-processor\input\16199001000074\ttbonline.gov\colasonline/" +  normalize_image_src(src),
                src=src,
                ocr_text="",
            )
        )

    return results