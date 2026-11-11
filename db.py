"""数据访问层：所有 SQL 都写在这里，不散落到接口函数里。

这样分层的好处：
  - 接口函数只管「收请求、返回响应」，不关心数据存哪
  - 想换成 MySQL，只改这个文件
  - 测试可以直接 import 这里查库，验证数据真写进去了
"""

import sqlite3

DB_PATH = "app.db"

SCHEMA = """
DROP TABLE IF EXISTS tasks;

CREATE TABLE tasks (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT    NOT NULL,
    done  INTEGER NOT NULL DEFAULT 0,
    owner TEXT    NOT NULL
);
"""

SEED = [
    ("写测试用例", 0, "admin"),
    ("跑自动化", 1, "admin"),
]


def get_conn():
    """拿一个连接。row_factory 让查询结果能按列名取值。"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """重建表并灌入初始数据。每次启动服务都重置，保证测试从确定状态开始。"""
    conn = get_conn()
    try:
        conn.executescript(SCHEMA)
        conn.executemany(
            "INSERT INTO tasks (title, done, owner) VALUES (?, ?, ?)", SEED
        )
        conn.commit()
    finally:
        conn.close()


def list_tasks():
    """查全部任务，返回 (总数, 列表)。"""
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT id, title, done, owner FROM tasks ORDER BY id"
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        return total, [dict(r) for r in rows]
    finally:
        conn.close()


def get_task(task_id):
    """按 id 查一条，查不到返回 None。"""
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT id, title, done, owner FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_task(title, done, owner):
    """插入一条并返回它（含自增 id）。"""
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO tasks (title, done, owner) VALUES (?, ?, ?)",
            (title, 1 if done else 0, owner),
        )
        conn.commit()
        new_id = cur.lastrowid
        row = conn.execute(
            "SELECT id, title, done, owner FROM tasks WHERE id = ?", (new_id,)
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


def count_tasks():
    """只查总数，用于一致性校验。"""
    conn = get_conn()
    try:
        return conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    finally:
        conn.close()
