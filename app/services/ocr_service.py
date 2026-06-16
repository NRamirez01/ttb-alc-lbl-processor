from html import escape
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Literal

import httpx
from PIL import Image, ImageDraw
from paddleocr import PaddleOCRVL, PaddleOCR

from app.models.schemas import OCRRegion, ImageResult
from app.utils.timing import Timer

OCRPreset = Literal["fast", "balanced", "quality"]

OCR_SERVER_URL = "http://localhost:8080"
OCR_SERVER_HEALTH_PATH = "/health"
OCR_SERVER_TIMEOUT_SECONDS = 1.0


def is_ocr_server_available(url: str = OCR_SERVER_URL) -> bool:
    try:
        with httpx.Client(timeout=OCR_SERVER_TIMEOUT_SECONDS) as client:
            response = client.get(f"{url}{OCR_SERVER_HEALTH_PATH}")
            return response.is_success
    except Exception:
        return False


def _preset_options(preset: OCRPreset) -> dict[str, Any]:
    if preset == "fast":
        return {
            "use_doc_orientation_classify": False,
            "use_doc_unwarping": False,
            "use_layout_detection": False,
            "merge_layout_blocks": True,
            "use_ocr_for_image_block": False,
            "format_block_content": False,
        }
    if preset == "balanced":
        return {
            "use_doc_orientation_classify": True,
            "use_doc_unwarping": False,
            "use_layout_detection": True,
            "merge_layout_blocks": False,
            "use_ocr_for_image_block": True,
            "format_block_content": False,
        }
    return {
        "use_doc_orientation_classify": True,
        "use_doc_unwarping": True,
        "use_layout_detection": True,
        "merge_layout_blocks": False,
        "use_ocr_for_image_block": True,
        "format_block_content": False,
    }


def build_server_ocr(preset: OCRPreset) -> PaddleOCRVL:
    return PaddleOCRVL(
        pipeline_version="v1.6",
        vl_rec_backend="llama-cpp-server",
        vl_rec_server_url=OCR_SERVER_URL,
        vl_rec_max_concurrency=2,
        **_preset_options(preset),
    )


def build_cpu_ocr() -> PaddleOCR:
    return PaddleOCR(
        device="cpu",
    )


# python -m venv .venv   
# .venv\Scripts\activate  
# python -m pip install --upgrade pip
# python -m pip install -r requirements.txt
class OCRService:
    def __init__(self) -> None:
        self.available = True
        self.output_dir = Path("output")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._ocr_instances: dict[tuple[str, OCRPreset], PaddleOCRVL] = {}

    def _build_backend_for_preset(self, preset: OCRPreset) -> tuple[PaddleOCRVL, str]:
        if is_ocr_server_available():
            try:
                return build_server_ocr(preset), "llama-cpp-server"
            except Exception as exc:
                print(f"OCR server backend failed during init for preset={preset}, falling back to CPU: {exc}")

        return build_cpu_ocr(), "cpu"

    def _get_ocr(self, preset: OCRPreset) -> tuple[PaddleOCRVL, str]:
        backend = "llama-cpp-server" if is_ocr_server_available() else "cpu"
        cache_key = (backend, preset)

        if cache_key not in self._ocr_instances:
            if backend == "llama-cpp-server":
                try:
                    self._ocr_instances[cache_key] = build_server_ocr(preset)
                except Exception:
                    backend = "cpu"
                    cache_key = (backend, preset)
                    self._ocr_instances[cache_key] = build_cpu_ocr()
            else:
                self._ocr_instances[cache_key] = build_cpu_ocr()

        return self._ocr_instances[cache_key], backend

    def _predict_with_fallback(self, image_path: str, preset: OCRPreset) -> tuple[list[Any], str]:
        ocr, backend = self._get_ocr(preset)

        try:
            return list(ocr.predict(image_path)), backend
        except Exception as exc:
            if backend == "llama-cpp-server":
                print(f"OCR server prediction failed for preset={preset}, falling back to CPU: {exc}")
                cpu_key = ("cpu", preset)
                if cpu_key not in self._ocr_instances:
                    self._ocr_instances[cpu_key] = build_cpu_ocr()
                return list(self._ocr_instances[cpu_key].predict(image_path)), "cpu"
            raise

    def extract_text(self, image_path: str, preset: OCRPreset = "quality") -> ImageResult:
        with Timer() as timer:
            result, backend = self._predict_with_fallback(image_path, preset)

        if not result:
            return ImageResult(
                image_type=Path(image_path).suffix.lower().lstrip("."),
                file_name=Path(image_path).name,
                src=image_path,
                ocr_text="",
                ocr_html=None,
                ocr_regions=[],
                annotated_src=None,
            )

        res_obj = result[0]
        res_obj.print()

        res_dict = res_obj.json
        image_result = self._build_image_result(
            file_name=Path(image_path).name,
            image_type=Path(image_path).suffix.lower().lstrip("."),
            src=image_path,
            paddle_result=res_dict,
            image_path=image_path,
            image_bytes=None,
        )

        print(f"OCR processing time: {timer.elapsed_ms} ms")
        print(f"OCR backend used: {backend}")
        print(f"OCR preset used: {preset}")
        return image_result

    def extract_text_from_bytes(
        self,
        image_bytes: bytes,
        file_name: str,
        src: str | None = None,
        preset: OCRPreset = "quality",
    ) -> ImageResult:
        suffix = Path(file_name).suffix or ".png"
        resolved_src = src or file_name

        with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(image_bytes)
            temp_path = Path(tmp.name)

        try:
            with Timer() as timer:
                result, backend = self._predict_with_fallback(str(temp_path), preset)

            if not result:
                return ImageResult(
                    image_type=suffix.lower().lstrip("."),
                    file_name=file_name,
                    src=resolved_src,
                    ocr_text="",
                    ocr_html=None,
                    ocr_regions=[],
                    annotated_src=None,
                )

            res_obj = result[0]
            res_obj.print()

            res_dict = res_obj.json
            image_result = self._build_image_result(
                file_name=file_name,
                image_type=suffix.lower().lstrip("."),
                src=resolved_src,
                paddle_result=res_dict,
                image_path=None,
                image_bytes=image_bytes,
            )

            print(f"OCR processing time: {timer.elapsed_ms} ms")
            print(f"OCR backend used: {backend}")
            print(f"OCR preset used: {preset}")
            return image_result
        finally:
            temp_path.unlink(missing_ok=True)

    def _build_image_result(
        self,
        *,
        file_name: str,
        image_type: str,
        src: str,
        paddle_result: dict[str, Any],
        image_path: str | None,
        image_bytes: bytes | None,
    ) -> ImageResult:
        res = paddle_result.get("res", {})
        parsing_res_list = res.get("parsing_res_list", [])
        layout_boxes = res.get("layout_det_res", {}).get("boxes", [])

        ocr_regions: list[OCRRegion] = []
        full_text_parts: list[str] = []
        full_html_parts: list[str] = []

        for block in parsing_res_list:
            text = (block.get("block_content") or "").strip()
            label = block.get("block_label", "")
            bbox = block.get("block_bbox", [])

            matching_box = self._find_matching_layout_box(layout_boxes, bbox, label)

            polygon_points = None
            score = None
            order = None

            if matching_box:
                raw_polygon = matching_box.get("polygon_points")
                if raw_polygon is not None:
                    polygon_points = raw_polygon
                score = matching_box.get("score")
                order = matching_box.get("order")

            region = OCRRegion(
                label=label,
                text=text,
                bbox=bbox,
                polygon_points=polygon_points,
                score=score,
                order=order,
            )
            ocr_regions.append(region)

            if text:
                full_text_parts.append(text)

                if "<table" in text.lower() and "</table>" in text.lower():
                    full_html_parts.append(text)
                else:
                    full_html_parts.append(escape(text).replace("\n", "<br/>"))

        annotated_path = self._annotated_output_path(file_name)
        self._draw_annotated_image(
            image_path=image_path,
            image_bytes=image_bytes,
            regions=ocr_regions,
            output_path=annotated_path,
        )

        return ImageResult(
            image_type=image_type,
            file_name=file_name,
            src=src or file_name,
            ocr_text="\n".join(full_text_parts) if full_text_parts else " ".join(res.get("rec_texts", [])),
            ocr_html="<br/>".join(full_html_parts) if full_html_parts else None,
            ocr_regions=ocr_regions,
            annotated_src=str(annotated_path),
            width=res.get("width"),
            height=res.get("height"),
        )

    def _find_matching_layout_box(
        self,
        layout_boxes: list[dict[str, Any]],
        bbox: list[int],
        label: str,
    ) -> dict[str, Any] | None:
        for box in layout_boxes:
            if box.get("coordinate") == bbox and box.get("label") == label:
                return box
        return None

    def _annotated_output_path(self, file_name: str) -> Path:
        image_file = Path(file_name)
        suffix = image_file.suffix or ".png"
        return self.output_dir / f"{image_file.stem}_annotated{suffix}"

    def _draw_annotated_image(
        self,
        *,
        image_path: str | None,
        image_bytes: bytes | None,
        regions: list[OCRRegion],
        output_path: Path,
    ) -> None:
        if image_bytes is not None:
            image = Image.open(BytesIO(image_bytes)).convert("RGB")
        elif image_path is not None:
            image = Image.open(image_path).convert("RGB")
        else:
            raise ValueError("Either image_path or image_bytes must be provided.")

        draw = ImageDraw.Draw(image)

        for region in regions:
            if not region.text:
                continue

            if region.polygon_points:
                points = [tuple(point) for point in region.polygon_points]
                draw.polygon(points, outline="red", width=3)
            elif len(region.bbox) == 4:
                x1, y1, x2, y2 = region.bbox
                draw.rectangle([x1, y1, x2, y2], outline="red", width=3)

        image.save(output_path)