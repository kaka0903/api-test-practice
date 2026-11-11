"""接口 ↔ 数据库 的一致性校验。

核心思想：**接口返回 201，只说明「服务说它成功了」，不说明数据真的落库。**

所以要绕过接口，直接查库确认。这是接口测试里最能抓出真问题的一类断言。
"""

import sqlite3

import requests

DB_PATH = "app.db"


def query_one(sql, params=()):
    """直接连数据库查一行。不经过服务，看到的是最原始的事实。"""
    conn = sqlite3.connect(DB_PATH)
    try:
        return conn.execute(sql, params).fetchone()
    finally:
        conn.close()


def test_创建的任务真的写进了数据库(base_url, auth_headers):
    """接口说成功 → 库里必须真的有。"""
    r = requests.post(
        f"{base_url}/tasks",
        json={"title": "数据库校验"},
        headers=auth_headers,
        timeout=5,
    )
    assert r.status_code == 201
    task_id = r.json()["id"]

    row = query_one("SELECT title, done, owner FROM tasks WHERE id = ?", (task_id,))
    assert row is not None, "接口返回成功，但数据库里查不到这条记录"
    assert row[0] == "数据库校验"
    assert row[1] == 0            # done 存的是 0/1
    assert row[2] == "admin"


def test_创建成功后总数加一(base_url, auth_headers):
    """创建前查一次、创建后再查一次，差值必须是 1。"""
    before = query_one("SELECT COUNT(*) FROM tasks")[0]

    r = requests.post(
        f"{base_url}/tasks",
        json={"title": "计数校验"},
        headers=auth_headers,
        timeout=5,
    )
    assert r.status_code == 201

    after = query_one("SELECT COUNT(*) FROM tasks")[0]
    assert after == before + 1


def test_标题为空被拒绝时数据库没有新增(base_url, auth_headers):
    """被拒绝的请求，绝不能留下脏数据。

    这条比「返回 422」更重要：返回码对了但数据仍写进去了，
    是真实项目里很难发现的一类缺陷。
    """
    before = query_one("SELECT COUNT(*) FROM tasks")[0]

    r = requests.post(
        f"{base_url}/tasks",
        json={"title": ""},
        headers=auth_headers,
        timeout=5,
    )
    assert r.status_code == 422

    after = query_one("SELECT COUNT(*) FROM tasks")[0]
    assert after == before, "请求被拒绝了，但数据库里还是多了一条"


def test_未授权的请求不会写入数据(base_url):
    """不带 token 创建任务，同样不能留数据。"""
    before = query_one("SELECT COUNT(*) FROM tasks")[0]

    r = requests.post(f"{base_url}/tasks", json={"title": "未授权"}, timeout=5)
    assert r.status_code == 401

    after = query_one("SELECT COUNT(*) FROM tasks")[0]
    assert after == before
