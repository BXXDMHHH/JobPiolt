import pytest
from db import database
from services.application_verification import record_application_check, list_application_checks


def test_verified_success_requires_evidence_and_updates_status(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DATA_DIR", tmp_path)
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()
    job_id = database.create_job(title="测试开发", company="示例公司", city="上海")
    with pytest.raises(ValueError):
        record_application_check(job_id, "已确认成功", "")
    check_id = record_application_check(job_id, "已确认成功", "页面明确显示已投递", "https://www.zhipin.com/job_detail/test")
    assert check_id > 0
    assert database.get_job(job_id)["status"] == "已投递"
    checks = list_application_checks(job_id)
    assert checks[0]["result"] == "已确认成功"
    assert "明确显示" in checks[0]["evidence"]
