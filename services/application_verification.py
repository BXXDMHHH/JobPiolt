"""投递结果证据记录。记录页面观察，不把按钮点击本身视为成功。"""
from typing import Any
from db.database import get_connection, init_db, JOB_STATUSES

RESULT_TYPES = ["已确认成功", "待核实", "投递失败"]
RESULT_TO_STATUS = {"已确认成功": "已投递", "待核实": "待核实", "投递失败": "投递失败"}


def record_application_check(job_id: int, result: str, evidence: str = "", page_url: str = "") -> int:
    if result not in RESULT_TYPES:
        raise ValueError(f"不支持的核实结果：{result}")
    if result == "已确认成功" and not evidence.strip():
        raise ValueError("确认成功必须填写页面证据，例如成功提示或已投递状态。")
    init_db()
    target_status = RESULT_TO_STATUS[result]
    if target_status not in JOB_STATUSES:
        raise ValueError(f"数据库不支持目标状态：{target_status}")
    with get_connection() as conn:
        job = conn.execute("SELECT id, status FROM jobs WHERE id=?", (job_id,)).fetchone()
        if job is None:
            raise ValueError("岗位不存在。")
        cursor = conn.execute(
            "INSERT INTO application_checks (job_id, result, evidence, page_url) VALUES (?, ?, ?, ?)",
            (job_id, result, evidence.strip(), page_url.strip()),
        )
        check_id = int(cursor.lastrowid)
        old_status = job["status"]
        if old_status != target_status:
            conn.execute(
                "UPDATE jobs SET status=?, updated_at=datetime('now', 'localtime') WHERE id=?",
                (target_status, job_id),
            )
            note = f"投递结果核实：{result}；证据：{evidence.strip()[:250] or '未提供补充证据'}"
            conn.execute(
                "INSERT INTO application_events (job_id, old_status, new_status, note) VALUES (?, ?, ?, ?)",
                (job_id, old_status, target_status, note),
            )
        return check_id


def list_application_checks(job_id: int | None = None) -> list[dict[str, Any]]:
    init_db()
    with get_connection() as conn:
        if job_id is None:
            rows = conn.execute(
                "SELECT c.*, j.title AS job_title, j.company FROM application_checks c JOIN jobs j ON j.id=c.job_id ORDER BY c.id DESC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT c.*, j.title AS job_title, j.company FROM application_checks c JOIN jobs j ON j.id=c.job_id WHERE c.job_id=? ORDER BY c.id DESC",
                (job_id,),
            ).fetchall()
        return [dict(row) for row in rows]
