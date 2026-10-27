"""本地简历文件管理。文件不上传到任何外部服务。"""
from hashlib import sha256
from pathlib import Path
import re

ROOT_DIR = Path(__file__).resolve().parents[1]
RESUME_DIR = ROOT_DIR / "resumes"
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt"}


def store_resume(uploaded_name: str, file_bytes: bytes) -> dict[str, str]:
    """安全地保存上传文件，并返回文件名与 SHA-256。"""
    suffix = Path(uploaded_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("仅支持 PDF、DOC、DOCX、TXT 格式。")
    if not file_bytes:
        raise ValueError("文件内容为空。")
    if len(file_bytes) > 15 * 1024 * 1024:
        raise ValueError("单份简历最大支持 15 MB。")
    RESUME_DIR.mkdir(parents=True, exist_ok=True)
    digest = sha256(file_bytes).hexdigest()
    safe_stem = re.sub(r"[^\w\-一-龥]+", "_", Path(uploaded_name).stem).strip("._")[:60] or "resume"
    filename = f"{safe_stem}_{digest[:12]}{suffix}"
    path = RESUME_DIR / filename
    if not path.exists():
        path.write_bytes(file_bytes)
    return {"stored_filename": filename, "sha256": digest}


def resolve_resume_path(stored_filename: str) -> Path:
    """仅允许访问 resumes 目录内的文件，防止路径穿越。"""
    path = (RESUME_DIR / stored_filename).resolve()
    if path.parent != RESUME_DIR.resolve():
        raise ValueError("无效的简历文件路径。")
    return path
