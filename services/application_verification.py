"""投递结果证据记录。记录页面观察，不把按钮点击本身视为成功。"""
from typing import Any
from db.database import get_connection, init_db

RESULT_TYPES = ["已确认成功", "待核实", "投递失败"]


def record_application_check(job_id: int, result: str, evidence: str = "", page_url: str = "") -> int:
    if result not in RESULT_TYPES:
        raise ValueError(f"不支持的核实结果：{result}")
    if result == "已确认成功" and not evidence.strip():
        raise ValueError("确认成功必须填写页面证据，例如成功提示或已投递状态。")
    init_db()
    with get_connection() as conn:
        exists = conn.execute("SELECT id FROM jobs WHERE id=?", (job_id,)).fetchone()
        if exists is None:
            raise ValueError("岗位不存在。")
        cursor = conn.execute(
            "INSERT INTO application_checks (job_id, result, evidence, page_url) VALUES (?, ?, ?, ?)",
            (job_id, result, evidence.strip(), page_url.strip()),
        )
        check_id = int(cursor.lastrowid)
        if result == "已确认成功":
            conn.execute("UPDATE jobs SET status='已投递', updated_at=datetime('now', 'localtime') WHERE id=?", (job_id,))
            conn.execute(
                "INSERT INTO application_events (job_id, old_status, new_status, note) VALUES (?, '待核实', '已投递', ?)",
                (job_id, "结果核实成功：" + evidence.strip()[:300]),
            )
        elif result == "投递失败":
            conn.execute("UPDATE jobs SET status='投递失败', updated_at=datetime('now', 'localtime') WHERE id=?", (job_id,))
            conn.execute(
                "INSERT INTO application_events (job_id, old_status, new_status, note) VALUES (?, '待核实', '投递失败', ?)",
                (job_id, "结果核实失败：" + (evidence.strip() or "用户确认投递失败")[:300]),
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
