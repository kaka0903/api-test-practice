"""pytest 公共配置：地址、token、以及「服务没启动」的友好提示。"""

import pytest
import requests

BASE_URL = "http://127.0.0.1:8000"


@pytest.fixture(scope="session")
def base_url():
    """所有测试共用的服务地址。改端口只需要改这里一行。"""
    return BASE_URL


@pytest.fixture(scope="session", autouse=True)
def server_alive(base_url):
    """开跑前先确认服务活着。

    autouse=True 表示每个测试都会用到它（自动执行，不用在参数里写）。
    好处：服务没起时，直接给一句人话，而不是 5 个看不懂的 ConnectionError。
    """
    try:
        requests.get(f"{base_url}/ping", timeout=2)
    except requests.exceptions.ConnectionError:
        pytest.exit(
            "\n服务没有启动。请另开一个终端，在 day12 目录下运行：\n"
            "    uvicorn server:app --reload\n",
            returncode=2,
        )


@pytest.fixture(scope="session")
def token(base_url):
    """登录一次，整个测试会话共用这个 token。

    scope="session" 是关键：不加这个，每个测试都会重新登录一次。
    20 条用例 = 20 次登录，又慢又没必要。
    """
    r = requests.post(
        f"{base_url}/login",
        json={"username": "admin", "password": "123456"},
        timeout=5,
    )
    assert r.status_code == 200, "登录失败，后面的鉴权用例都没法跑"
    return r.json()["token"]


@pytest.fixture(scope="session")
def auth_headers(token):
    """把 token 拼成 Authorization 头，省得每个测试都写一遍。"""
    return {"Authorization": f"Bearer {token}"}
