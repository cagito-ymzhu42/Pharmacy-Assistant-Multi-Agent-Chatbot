from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel, Field

# ========== Pydantic 输出模型定义 ==========
class UserProfile(BaseModel):
    age: Optional[str] = Field(None, description="用户的年龄")
    condition: Optional[str] = Field(None, description="用户的病情、症状或疾病")
    health_background: Optional[str] = Field(None, description="用户的健康背景，如'高血压'、'怀孕'等")
    region: Optional[str] = Field(None, description="用户所在地区，如'港岛'、'九龙'、'新界'或具体地点")

class DrugCandidate(BaseModel):
    drug_name: str
    reason: str
    score: float

class Recommendation(BaseModel):
    recommended_drugs: List[DrugCandidate]

class CheckerFeedback(BaseModel):
    is_safe: bool
    risks: List[str]
    conclusion: str = Field(
        description="对整个方案的最终结论和思考过程的总结。这段话将可能直接展示给用户，所以需要专业、清晰、易于理解。如果方案安全，总结为何安全；如果不安全，总结核心风险并给出建议。"
    )

# ========== Agent 状态定义 ==========
class AgentState(TypedDict):
    messages: List[Any]
    profile: Dict[str, Any]
    candidates: List[Dict[str, Any]]
    checker_feedback: Optional[Dict[str, Any]]
    session_complete: bool