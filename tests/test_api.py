"""接口自动化测试：先跑通这 5 条，再往下扩。

运行前必须先启动服务（另开终端，在 day12 目录）：
    uvicorn server:app --reload

然后在这里运行：
    pytest -v

每个 test_ 函数 = 用例表里的一行。
函数名说清测什么，assert 说清期望什么。
"""

import requests
import pytest


# ==================== TC-001 ====================
def test_ping_服务存活(base_url):
    """健康检查：服务能响应就说明活着。"""
    r = requests.get(f"{base_url}/ping", timeout=5)

    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ==================== TC-003 ====================
def test_登录成功返回token(base_url):
    """正确账号密码登录，应当拿到非空 token。"""
    r = requests.post(
        f"{base_url}/login",
        json={"username": "admin", "password": "123456"},
        timeout=5,
    )

    assert r.status_code == 200
    body = r.json()
    assert "token" in body
    assert body["token"] != "", "token 不应该为空"


# ==================== TC-008 ====================
def test_不带token查任务返回401(base_url):
    """没带凭证就想看数据，必须被拦。"""
    r = requests.get(f"{base_url}/tasks", timeout=5)

    assert r.status_code == 401


# ==================== TC-010 ====================
def test_带token查任务成功(base_url, auth_headers):
    """带凭证能查到，并且 total 要和 data 的实际条数对得上。"""
    r = requests.get(f"{base_url}/tasks", headers=auth_headers, timeout=5)

    assert r.status_code == 200
    body = r.json()

    # 这一行是重点：统计字段和明细数组必须一致
    assert body["total"] == len(body["data"])

# ==================== TC-002 ====================
def test_post_ping_返回405(base_url):
    """POST 方法访问只支持 GET 的接口，应返回 405。"""
    r = requests.post(f"{base_url}/ping", timeout=5)

    assert r.status_code == 405

@pytest.mark.parametrize("username, password, expected", [
    ("admin",  "123456", 200),   # 正常登录
    ("admin",  "wrong",  401),   # 密码错
    ("nobody", "123456", 401),   # 用户不存在
    ("",       "",       401),   # 都为空
],ids=["正常", "密码错", "用户不存在", "都为空"])


def test_登录(base_url, username, password, expected):
    r = requests.post(f"{base_url}/login",
                      json={"username": username, "password": password},
                      timeout=5)
    assert r.status_code == expected

# ==================== TC-016（已知缺陷，预期会失败）====================
def test_创建任务时标题不能为空(base_url, auth_headers):
    """标题为空时应当被拒绝（422），而不是成功创建（201）。"""
    r = requests.post(
        f"{base_url}/tasks",
        json={"title": ""},
        headers=auth_headers,
        timeout=5,
    )

    assert r.status_code == 422