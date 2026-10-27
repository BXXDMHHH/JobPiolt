from pathlib import Path
import pytest
from services import resume_service


def test_store_resume_hashes_and_reuses_same_file(tmp_path, monkeypatch):
    monkeypatch.setattr(resume_service, "RESUME_DIR", tmp_path)
    first = resume_service.store_resume("测试简历.pdf", b"sample pdf bytes")
    second = resume_service.store_resume("../测试简历.pdf", b"sample pdf bytes")
    assert first == second
    assert (tmp_path / first["stored_filename"]).read_bytes() == b"sample pdf bytes"
    assert len(first["sha256"]) == 64


def test_reject_unsupported_or_empty_resume(tmp_path, monkeypatch):
    monkeypatch.setattr(resume_service, "RESUME_DIR", tmp_path)
    with pytest.raises(ValueError):
        resume_service.store_resume("resume.exe", b"not allowed")
    with pytest.raises(ValueError):
        resume_service.store_resume("resume.pdf", b"")


def test_resolve_resume_path_blocks_path_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(resume_service, "RESUME_DIR", tmp_path)
    with pytest.raises(ValueError):
        resume_service.resolve_resume_path("../secret.txt")
