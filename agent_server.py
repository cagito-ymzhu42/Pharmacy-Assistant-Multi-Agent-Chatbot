import copy
import sys
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# 检查核心模块是否加载成功
from core.config import check_modules_loaded
if not check_modules_loaded():
    sys.exit(1)

# 导入编译好的工作流和初始状态模板
from agents.workflow import app
from core.models import AgentState

# --- FastAPI 应用设置 ---
api = FastAPI(
    title="智能药房Agent API",
    description="一个通过API暴露的多智能体药房导购服务",
    version="1.0.0",
)

# --- 会话状态管理 ---
# 注意：这是一个简单的内存存储，不适用于生产环境。
# 在生产中，应使用Redis、数据库或其他持久化存储。
session_states: dict[str, AgentState] = {}

initial_state_template: AgentState = {
    "messages": [],
    "profile": {},
    "candidates": [],
    "checker_feedback": None,
    "session_complete": False,
}

# --- API 请求和响应模型 ---
class ChatRequest(BaseModel):
    query: str
    session_id: str | None = Field(None, description="会话ID。如果为空，将创建一个新会话。")

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    session_complete: bool

# --- API 端点 ---
@api.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    """
    与智能药房Agent进行对话。
    """
    session_id = request.session_id or str(uuid.uuid4())
    
    # 获取或创建会话状态
    current_state = session_states.get(session_id)
    if not current_state:
        current_state = copy.deepcopy(initial_state_template)

    # 更新状态
    current_state["messages"].append(("user", request.query))
    current_state["session_complete"] = False

    # 调用Agent工作流
    try:
        final_state = app.invoke(current_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent执行出错: {e}")

    # 提取最终回复
    last_msg_for_user = "抱歉，我无法处理您的请求。"
    if final_state.get("messages"):
        for msg in reversed(final_state["messages"]):
            if hasattr(msg, 'content') and msg.content and not hasattr(msg, 'tool_calls'):
                last_msg_for_user = msg.content
                break
            elif isinstance(msg, str):
                last_msg_for_user = msg
                break

    # 更新或清除会话状态
    session_complete = final_state.get("session_complete", False)
    if session_complete:
        if session_id in session_states:
            del session_states[session_id]
        print(f"--- [Server] 会话 {session_id} 已结束并清除。 ---")
    else:
        session_states[session_id] = final_state
        print(f"--- [Server] 会话 {session_id} 已更新。 ---")

    return ChatResponse(
        reply=last_msg_for_user,
        session_id=session_id,
        session_complete=session_complete
    )

@api.get("/")
def root():
    return {"message": "智能药房Agent服务器已启动。请访问 /docs 查看API文档。"}

if __name__ == "__main__":
    import uvicorn
    print("启动FastAPI服务器，访问 http://127.0.0.1:8000")
    uvicorn.run(api, host="127.0.0.1", port=8000)