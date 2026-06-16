from pathlib import Path
from uuid import uuid4


def stage_uploaded_html(html_bytes: bytes, filename: str) -> Path:
    safe_name = Path(filename or "application.html").name
    job_id = uuid4().hex

    work_dir = Path("working") / "applications" / job_id
    work_dir.mkdir(parents=True, exist_ok=True)

    html_path = work_dir / safe_name
    html_path.write_bytes(html_bytes)

    return html_path