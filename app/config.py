from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TMP_DIR = BASE_DIR / "tmp"
UPLOAD_DIR = TMP_DIR / "uploads"

OCR_ENABLED = True
OCR_LANGUAGE = "en"
PROCESS_TIMEOUT_SECONDS = 5