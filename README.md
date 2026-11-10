# 任务管理 API · 接口自动化测试

一个用于练习**接口测试**的项目：自己写一个极简 API，然后像真实测试岗那样
——设计用例、执行、发现缺陷、写自动化、持续回归。

## 被测服务

`server.py` 是一个 90 行的 FastAPI 服务，5 个接口：

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| GET | `/ping` | 健康检查 | 否 |
| POST | `/login` | 登录，返回 token | 否 |
| GET | `/tasks` | 任务列表 | 是 |
| POST | `/tasks` | 新建任务（201） | 是 |
| GET | `/tasks/{id}` | 按 id 查任务 | 否 |

数据存在内存里，重启即清空——保证每次测试从确定状态开始。

## 运行

```bash
pip install -r requirements-dev.txt

# 终端 A：启动被测服务
uvicorn server:app --reload

# 终端 B：跑测试
pytest -v
```

打开 http://127.0.0.1:8000/docs 可以看到 FastAPI 自动生成的接口文档。

## 目录结构

```
server.py                  被测服务（FastAPI）
conftest.py                测试公共配置：base_url / token / 服务存活检查
pytest.ini                 pytest 配置
requirements-dev.txt       开发依赖
tests/test_api.py          接口自动化测试，10 条
```

## 关键设计

**session 级 token fixture**：登录只做一次，所有用例共用，避免 N 条用例登录 N 次。

```python
@pytest.fixture(scope="session")
def token(base_url):
    r = requests.post(f"{base_url}/login", json={...})
    return r.json()["token"]
```

**服务存活检查**：每个测试自动执行，服务没起时给出人话提示，而不是一堆
`ConnectionError`。

**参数化**：同一组逻辑用不同数据跑多次，一个函数覆盖多条用例。

```python
@pytest.mark.parametrize("username, password, expected", [
    ("admin", "123456", 200),
    ("admin", "wrong",  401),
], ids=["正常", "密码错"])
```

## 覆盖范围

| 分类 | 用例 |
|---|---|
| 健康检查 | 服务存活、方法不允许（405） |
| 登录（参数化） | 正常、密码错、用户不存在、都为空 |
| 鉴权 | 不带 token（401）、带 token 正常访问 |
| 数据一致性 | `total` 与 `data` 长度一致 |
| 参数校验 | 标题为空时应返回 422 |

## 已发现的缺陷

| 编号 | 现象 | 根因 | 状态 |
|---|---|---|---|
| BUG-003 | `Authorization` 缺少 `Bearer` 前缀仍然通过 | 用 `replace("Bearer ", "")` 取 token，无前缀时原样返回，恰好命中 | 待确认（是否强制 Bearer 规范） |
| BUG-004 | 创建任务时 `title` 传空字符串返回 201 | `title: str` 未做非空校验 | 已修复（`Field(min_length=1)`），回归通过 |

## 待补充

- [ ] 标题为纯空格串的校验（空格串不是空串）
- [ ] 创建后 `total` +1 的一致性断言
- [ ] id 为 0 / 负数的边界用例
- [ ] 接入 GitHub Actions
