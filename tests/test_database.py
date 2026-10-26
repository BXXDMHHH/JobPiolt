from db import database


def test_create_edit_status_and_history(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DATA_DIR", tmp_path)
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()
    job_id = database.create_job(title="测试开发", company="示例公司", city="上海")
    database.update_job(job_id, title="软件测试开发", company="示例公司", city="上海", salary="10-15K")
    assert database.get_job(job_id)["title"] == "软件测试开发"
    assert database.get_job(job_id)["salary"] == "10-15K"
    assert database.update_job_status(job_id, "已投递", "页面显示投递成功") is True
    assert database.get_job(job_id)["status"] == "已投递"
    events = database.list_application_events(job_id)
    assert len(events) == 2
    assert events[0]["old_status"] == "待投递"
    assert events[0]["new_status"] == "已投递"
    assert events[0]["note"] == "页面显示投递成功"


def test_csv_import_skips_duplicates_and_invalid_rows(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DATA_DIR", tmp_path)
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()
    rows = [
        {"岗位名称": "测试工程师", "公司名称": "甲公司", "城市": "上海"},
        {"岗位名称": "测试工程师", "公司名称": "甲公司", "城市": "上海"},
        {"岗位名称": "", "公司名称": "缺少岗位名"},
    ]
    assert database.import_jobs(rows) == {"imported": 1, "skipped": 1, "failed": 1}
    assert database.count_jobs() == 1
