from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw
from paddleocr import PaddleOCRVL

from app.models.schemas import OCRRegion, ImageResult
from app.utils.timing import Timer


ocr = PaddleOCRVL(
    pipeline_version="v1.6",
    vl_rec_backend="llama-cpp-server",
    vl_rec_server_url="http://localhost:8080",
    vl_rec_max_concurrency=2,
    use_doc_orientation_classify=True,
    use_doc_unwarping=True,
    use_layout_detection=True, # Greatly changes speed
    merge_layout_blocks=False,
    use_ocr_for_image_block=True,
    format_block_content=False,
)


# For crooked labels.
# ocr = PaddleOCRVL(
#     pipeline_version="v1.6",
#     vl_rec_backend="llama-cpp-server",
#     vl_rec_server_url="http://localhost:8080",
#     vl_rec_max_concurrency=2,

#     use_doc_orientation_classify=True,
#     use_doc_unwarping=True,
#     use_layout_detection=True,

#     use_chart_recognition=False,
#     use_seal_recognition=False,
#     use_ocr_for_image_block=False,
#     format_block_content=False,
#     merge_layout_blocks=True,
# )

# llama-server `
#   -m "C:\Users\nrami\Desktop\Code\ttb-alc-lbl-processor\models\PaddleOCR-VL-1.6-GGUF.gguf" `
#   --mmproj "C:\Users\nrami\Desktop\Code\ttb-alc-lbl-processor\models\PaddleOCR-VL-1.6-GGUF-mmproj.gguf" `
#   --host 0.0.0.0 `
#   --port 8080 `
#   --temp 0 `
#   --n-gpu-layers 999 `
#   --ctx-size 16384 `
#   --parallel 2

# llama-server `
#   -m "C:\Users\nrami\Desktop\Code\ttb-alc-lbl-processor\models\PaddleOCR-VL-1.6-GGUF.gguf" `
#   --mmproj "C:\Users\nrami\Desktop\Code\ttb-alc-lbl-processor\models\PaddleOCR-VL-1.6-GGUF-mmproj.gguf" `
#   --host 0.0.0.0 `
#   --port 8080 `
#   --temp 0 `
#   --n-gpu-layers 999 `
#   --ctx-size 32768 `
#   --parallel 4

# llama-server `
#   -m "C:\Users\nrami\Desktop\Code\ttb-alc-lbl-processor\models\PaddleOCR-VL-1.6-GGUF.gguf" `
#   --mmproj "C:\Users\nrami\Desktop\Code\ttb-alc-lbl-processor\models\PaddleOCR-VL-1.6-GGUF-mmproj.gguf" `
#   --host 0.0.0.0 `
#   --port 8080 `
#   --temp 0 `
#   --n-gpu-layers 999 `
#   --ctx-size 32768 `
#   --parallel 2

class OCRService:
    def __init__(self) -> None:
        self.available = True
        self.output_dir = Path("output")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_text(self, image_path: str) -> ImageResult:
        with Timer() as timer:
            result = list(ocr.predict(image_path))

        if not result:
            return ImageResult(
                image_type=Path(image_path).suffix.lower().lstrip("."),
                file_name=Path(image_path).name,
                src=image_path,
                ocr_text="",
                ocr_regions=[],
                annotated_src=None,
            )

        res_obj = result[0]
        res_obj.print()
        # res_obj.save_to_img(str(self.output_dir))
        # res_obj.save_to_json(str(self.output_dir))

        res_dict = res_obj.json
        image_result = self._build_image_result(image_path, res_dict)

        print(f"OCR processing time: {timer.elapsed_ms} ms")
        return image_result

    def _build_image_result(self, image_path: str, paddle_result: dict[str, Any]) -> ImageResult:
        res = paddle_result.get("res", {})
        parsing_res_list = res.get("parsing_res_list", [])
        layout_boxes = res.get("layout_det_res", {}).get("boxes", [])

        ocr_regions: list[OCRRegion] = []
        full_text_parts: list[str] = []

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

        annotated_path = self._annotated_output_path(image_path)
        self._draw_annotated_image(image_path, ocr_regions, annotated_path)

        return ImageResult(
            image_type=Path(image_path).suffix.lower().lstrip("."),
            file_name=Path(image_path).name,
            src=image_path,
            ocr_text="\n".join(full_text_parts),
            ocr_regions=ocr_regions,
            annotated_src=str(annotated_path),
            width=res.get("width"),
            height=res.get("height"),
        )

    def _find_matching_layout_box(self, layout_boxes: list[dict[str, Any]], bbox: list[int], label: str) -> dict[str, Any] | None:
        for box in layout_boxes:
            if box.get("coordinate") == bbox and box.get("label") == label:
                return box
        return None

    def _annotated_output_path(self, image_path: str) -> Path:
        image_file = Path(image_path)
        return self.output_dir / f"{image_file.stem}_annotated{image_file.suffix}"

    def _draw_annotated_image(self, image_path: str, regions: list[OCRRegion], output_path: Path) -> None:
        image = Image.open(image_path).convert("RGB")
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


# wget --page-requisites --convert-links --adjust-extensionn https://ttbonline.gov/colasonline/viewColaDetails.do?action=publicFormDisplay&ttbid=12243001000461

# wget --page-requisites --convert-links --adjust-extensionn https://ttbonline.gov/colasonline/viewColaDetails.do?action=publicFormDisplay&ttbid=16199001000074

# wget -P 12243001000461 \
#   --page-requisites \
#   --convert-links \
#   --adjust-extension \
#   "https://ttbonline.gov/colasonline/viewColaDetails.do?action=publicFormDisplay&ttbid=12243001000461" \
#   --no-check-certificate


# wget -P 16199001000074 \
#   --page-requisites \
#   --convert-links \
#   --adjust-extension \
#   "https://ttbonline.gov/colasonline/viewColaDetails.do?action=publicFormDisplay&ttbid=16199001000074" \
#   --no-check-certificate

