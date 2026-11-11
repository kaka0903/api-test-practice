"""极简「任务管理 API」。

数据存在 SQLite（app.db）里，不再放内存——这样才能练习「接口说成功，
去库里查证」这个真实测试动作。

启动：
    uvicorn server:app --reload

接口文档：
    http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

import db

app = FastAPI(title="Day12 被测服务", version="1.1")

# 启动即重置数据库，保证每次测试都从确定状态开始
db.init_db()

# ---------- 账号与 token（不属于业务数据，放内存够用） ----------
USERS = {"admin": "123456"}
TOKENS = {}          # token -> username


def current_user(authorization: str) -> str:
    """从 Authorization 头里取出用户，无效则抛 401。"""
    token = authorization.replace("Bearer ", "").strip()
    if token not in TOKENS:
        raise HTTPException(status_code=401, detail="未登录或 token 无效")
    return TOKENS[token]


def to_api(row: dict) -> dict:
    """数据库里的 done 是 0/1，转成 API 约定的布尔值。"""
    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"]),
        "owner": row["owner"],
    }


# ---------- 请求体模型 ----------
class LoginIn(BaseModel):
    username: str
    password: str


class TaskIn(BaseModel):
    # min_length=1 表示标题至少 1 个字符，空字符串会被拦在参数层（返回 422）
    # 这行是修复 BUG-004 的关键
    title: str = Field(..., min_length=1, description="任务标题，不能为空")
    done: bool = False


# ---------- 接口 ----------
@app.get("/ping")
def ping():
    """健康检查，不需要鉴权。"""
    return {"status": "ok"}


@app.post("/login")
def login(data: LoginIn):
    """登录成功返回 token；用户名或密码错误返回 401。"""
    if USERS.get(data.username) != data.password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = f"fake-token-{data.username}"
    TOKENS[token] = data.username
    return {"token": token, "username": data.username}


@app.get("/tasks")
def list_tasks(authorization: str = Header(default="")):
    """查询任务列表，需要 Authorization: Bearer <token>。"""
    current_user(authorization)
    total, rows = db.list_tasks()
    return {"total": total, "data": [to_api(r) for r in rows]}


@app.post("/tasks", status_code=201)
def create_task(data: TaskIn, authorization: str = Header(default="")):
    """新建任务，成功返回 201。"""
    owner = current_user(authorization)
    row = db.create_task(data.title, data.done, owner)
    return to_api(row)


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    """按 id 查任务；不存在返回 404，id 不是整数返回 422。"""
    row = db.get_task(task_id)
    if row is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return to_api(row)
