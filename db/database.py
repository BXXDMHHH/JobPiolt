"""SQLite 数据访问层。

28 法则：掌握 sqlite3.connect、execute、commit 和查询结果转换，
就能完成大多数本地小工具的数据持久化。
"""
from pathlib import Path
import sqlite3
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "jobpilot.db"


def get_connection() -> sqlite3.Connection:
    """创建连接，并让查询结果可以通过列名读取。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """初始化表结构；重复运行不会删除已有数据。"""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                city TEXT NOT NULL DEFAULT '',
                salary TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL DEFAULT '',
                jd TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT '待投递',
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                UNIQUE(title, company, city)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS application_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                old_status TEXT,
                new_status TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
            )
        """)


def create_job(*, title: str, company: str, city: str = "", salary: str = "", url: str = "", jd: str = "") -> int:
    """新增岗位；相同岗位名称、公司和城市视为重复。"""
    init_db()
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO jobs (title, company, city, salary, url, jd) VALUES (?, ?, ?, ?, ?, ?)",
                (title, company, city, salary, url, jd),
            )
            job_id = int(cursor.lastrowid)
            conn.execute(
                "INSERT INTO application_events (job_id, old_status, new_status, note) VALUES (?, NULL, '待投递', '创建岗位')",
                (job_id,),
            )
            return job_id
    except sqlite3.IntegrityError as exc:
        raise ValueError("疑似重复岗位：相同岗位名称、公司和城市已存在。") from exc


def list_jobs() -> list[dict[str, Any]]:
    """按创建时间倒序返回岗位列表。"""
    init_db()
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM jobs ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]


def count_jobs() -> int:
    """返回岗位总数。"""
    init_db()
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS total FROM jobs").fetchone()
        return int(row["total"])
