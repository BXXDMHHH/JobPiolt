"""SQLite 数据访问层。掌握连接、参数化 SQL、commit 和查询结果转换，就能完成本地工具的数据持久化。"""
from pathlib import Path
import sqlite3
from contextlib import contextmanager
from typing import Any, Iterator

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "jobpilot.db"
JOB_STATUSES = ["待投递", "准备中", "待确认", "已投递", "待沟通", "面试", "已拒绝", "已录用", "已撤回", "投递失败"]


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """提供自动提交/回滚并关闭连接的数据库上下文。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """初始化表结构，不删除已有数据。"""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL, company TEXT NOT NULL,
                city TEXT NOT NULL DEFAULT '', salary TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL DEFAULT '', jd TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT '待投递',
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                UNIQUE(title, company, city)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS application_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL, old_status TEXT,
                new_status TEXT NOT NULL, note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
            )
        """)


def create_job(*, title: str, company: str, city: str = "", salary: str = "", url: str = "", jd: str = "", status: str = "待投递") -> int:
    """新增岗位，并记录初始状态。"""
    init_db()
    if status not in JOB_STATUSES:
        raise ValueError(f"不支持的状态：{status}")
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO jobs (title, company, city, salary, url, jd, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (title.strip(), company.strip(), city.strip(), salary.strip(), url.strip(), jd.strip(), status),
            )
            job_id = int(cursor.lastrowid)
            conn.execute(
                "INSERT INTO application_events (job_id, old_status, new_status, note) VALUES (?, NULL, ?, ?)",
                (job_id, status, "创建岗位"),
            )
            return job_id
    except sqlite3.IntegrityError as exc:
        raise ValueError("疑似重复岗位：相同岗位名称、公司和城市已存在。") from exc


def list_jobs() -> list[dict[str, Any]]:
    init_db()
    with get_connection() as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM jobs ORDER BY id DESC").fetchall()]


def get_job(job_id: int) -> dict[str, Any] | None:
    init_db()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        return dict(row) if row else None


def update_job(job_id: int, *, title: str, company: str, city: str = "", salary: str = "", url: str = "", jd: str = "") -> None:
    """编辑岗位信息，不覆盖投递状态。"""
    init_db()
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                """UPDATE jobs SET title=?, company=?, city=?, salary=?, url=?, jd=?,
                updated_at=datetime('now', 'localtime') WHERE id=?""",
                (title.strip(), company.strip(), city.strip(), salary.strip(), url.strip(), jd.strip(), job_id),
            )
            if cursor.rowcount == 0:
                raise ValueError("岗位不存在，可能已被删除。")
    except sqlite3.IntegrityError as exc:
        raise ValueError("修改后与其他岗位重复，请检查岗位名称、公司和城市。") from exc


def update_job_status(job_id: int, new_status: str, note: str = "") -> bool:
    """更新状态并写入历史。返回状态是否发生变化。"""
    init_db()
    if new_status not in JOB_STATUSES:
        raise ValueError(f"不支持的状态：{new_status}")
    with get_connection() as conn:
        row = conn.execute("SELECT status FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            raise ValueError("岗位不存在，可能已被删除。")
        old_status = row["status"]
        if old_status == new_status and not note.strip():
            return False
        conn.execute(
            "UPDATE jobs SET status=?, updated_at=datetime('now', 'localtime') WHERE id=?",
            (new_status, job_id),
        )
        conn.execute(
            "INSERT INTO application_events (job_id, old_status, new_status, note) VALUES (?, ?, ?, ?)",
            (job_id, old_status, new_status, note.strip() or "状态更新"),
        )
        return old_status != new_status


def list_application_events(job_id: int | None = None, limit: int = 500) -> list[dict[str, Any]]:
    """查看单个岗位或所有岗位最近的状态历史。"""
    init_db()
    with get_connection() as conn:
        if job_id is None:
            query = """SELECT e.*, j.title AS job_title, j.company AS company
                       FROM application_events e JOIN jobs j ON j.id=e.job_id
                       ORDER BY e.id DESC LIMIT ?"""
            rows = conn.execute(query, (limit,)).fetchall()
        else:
            query = """SELECT e.*, j.title AS job_title, j.company AS company
                       FROM application_events e JOIN jobs j ON j.id=e.job_id
                       WHERE e.job_id=? ORDER BY e.id DESC LIMIT ?"""
            rows = conn.execute(query, (job_id, limit)).fetchall()
        return [dict(row) for row in rows]


def import_jobs(rows: list[dict[str, Any]]) -> dict[str, int]:
    """批量导入岗位；重复记录跳过，返回导入/跳过/失败数量。"""
    imported = skipped = failed = 0
    for row in rows:
        title = str(row.get("title", row.get("岗位名称", row.get("岗位", ""))) or "").strip()
        company = str(row.get("company", row.get("公司名称", row.get("公司", ""))) or "").strip()
        if not title or not company:
            failed += 1
            continue
        city = str(row.get("city", row.get("城市", "")) or "").strip()
        salary = str(row.get("salary", row.get("薪资", "")) or "").strip()
        url = str(row.get("url", row.get("岗位链接", row.get("链接", ""))) or "").strip()
        jd = str(row.get("jd", row.get("岗位描述", row.get("JD", ""))) or "").strip()
        status = str(row.get("status", row.get("状态", "待投递")) or "待投递").strip()
        if status not in JOB_STATUSES:
            status = "待投递"
        try:
            create_job(title=title, company=company, city=city, salary=salary, url=url, jd=jd, status=status)
            imported += 1
        except ValueError:
            skipped += 1
    return {"imported": imported, "skipped": skipped, "failed": failed}


def count_jobs() -> int:
    init_db()
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS total FROM jobs").fetchone()
        return int(row["total"])
