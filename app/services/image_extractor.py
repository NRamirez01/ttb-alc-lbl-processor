from pathlib import Path
from urllib.parse import parse_qs, unquote, urljoin, urlparse
from uuid import uuid4
import re

import httpx
from bs4 import BeautifulSoup

from app.models.schemas import ImageResult


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

async def extract_ttb_assets_from_remote_html(
    html_text: str,
    base_url: str,
    client: httpx.AsyncClient,
) -> tuple[str, list[ImageResult]]:
    soup = BeautifulSoup(html_text, "html.parser")

    signature_src = ""
    label_images: list[ImageResult] = []

    job_id = uuid4().hex
    output_dir = Path("static") / "remote_labels" / job_id
    output_dir.mkdir(parents=True, exist_ok=True)

    label_index = 0

    for img in soup.find_all("img"):
        raw_src = (img.get("src") or "").strip()
        if not raw_src:
            continue



        full_src = urljoin(base_url, raw_src)
        parsed = urlparse(full_src)
        path_lower = parsed.path.lower()
        query = parse_qs(parsed.query)

        print("IMG RAW SRC:", raw_src)
        print("IMG FULL SRC:", full_src)
        print("OUTPUT DIR:", output_dir)

        request_headers = {
            "Referer": base_url,
            "User-Agent": "Mozilla/5.0",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        }

        if "publicviewsignature.do" in path_lower:
            try:
                response = await client.get(full_src, headers=request_headers)
                response.raise_for_status()
            except Exception:
                continue

            content_type = response.headers.get("content-type", "").lower()
            if "text/html" in content_type or not content_type.startswith("image/"):
                continue

            suffix = ".png"
            if "jpeg" in content_type or "jpg" in content_type:
                suffix = ".jpg"
            elif "gif" in content_type:
                suffix = ".gif"
            elif "webp" in content_type:
                suffix = ".webp"

            signature_name = f"signature{suffix}"
            signature_path = output_dir / signature_name
            signature_path.write_bytes(response.content)

            signature_src = f"/static/remote_labels/{job_id}/{signature_name}"
            continue

        if "publicviewattachment.do" in path_lower:
            filename = query.get("filename", [""])[0].strip()
            if not filename:
                filename = f"label-{label_index + 1}.jpg"

            suffix = Path(filename).suffix.lower()
            if suffix not in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
                continue

            try:
                response = await client.get(full_src, headers=request_headers)
                response.raise_for_status()
            except Exception:
                continue

            content_type = response.headers.get("content-type", "").lower()
            if "text/html" in content_type or not content_type.startswith("image/"):
                continue

            local_name = f"label-{label_index + 1}{suffix or '.jpg'}"
            local_path = output_dir / local_name
            local_path.write_bytes(response.content)

            label_images.append(
                ImageResult(
                    image_type=(suffix.lstrip(".") or "jpg"),
                    file_name=filename,
                    src=f"/static/remote_labels/{job_id}/{local_name}",
                    ocr_text="",
                    ocr_regions=[],
                    annotated_src=None,
                )
            )
            label_index += 1

    return signature_src, label_images