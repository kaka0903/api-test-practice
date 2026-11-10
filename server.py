"""极简「任务管理 API」。

启动：
    uvicorn server:app --reload


"""

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Day12 被测服务", version="1.0")

# ---------- 内存数据 ----------
USERS = {"admin": "123456"}
TOKENS = {}          # token -> username
TASKS = [
    {"id": 1, "title": "写测试用例", "done": False, "owner": "admin"},
    {"id": 2, "title": "跑自动化", "done": True, "owner": "admin"},
]


def current_user(authorization: str) -> str:
    """从 Authorization 头里取出用户，无效则抛 401。"""
    token = authorization.replace("Bearer ", "").strip()
    if token not in TOKENS:
        raise HTTPException(status_code=401, detail="未登录或 token 无效")
    return TOKENS[token]


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
    return {"total": len(TASKS), "data": TASKS}


@app.post("/tasks", status_code=201)
def create_task(data: TaskIn, authorization: str = Header(default="")):
    """新建任务，成功返回 201。"""
    owner = current_user(authorization)

    task = {
        "id": max([t["id"] for t in TASKS], default=0) + 1,
        "title": data.title,
        "done": data.done,
        "owner": owner,
    }
    TASKS.append(task)
    return task


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    """按 id 查任务；不存在返回 404，id 不是整数返回 422。"""
    for t in TASKS:
        if t["id"] == task_id:
            return t
    raise HTTPException(status_code=404, detail="任务不存在")
