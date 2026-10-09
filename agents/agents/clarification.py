from typing import Dict, Any
from core.models import AgentState
from core.config import llm

def clarification_agent(state: AgentState) -> Dict[str, Any]:
    """当用户画像信息不完整时，生成针对性的问题进行追问。"""
    print("--- [Agent] 澄清 Agent 正在工作 ---")
    profile = state.get("profile", {})
    
    missing_info = []
    if not profile.get("age"): missing_info.append("age")
    if not profile.get("condition"): missing_info.append("symptoms or condition")
    if not profile.get("health_background"): missing_info.append("health background, including conditions, allergies, pregnancy or breastfeeding")
    
    if not missing_info:
        return {"messages": state["messages"] + ["Could you tell me a little more about what you need?"]}

    prompt = f"""You are a helpful Hong Kong pharmacy enquiry assistant.
    Ask a concise English follow-up question for only the missing information.
    Missing information: {', '.join(missing_info)}.
    Known profile: {profile}.
    The user can explicitly state that they have no known conditions or allergies.
    """

    try:
        clarification_question = llm.invoke(prompt).content.strip()
    except Exception as e:
        print(f"生成澄清问题失败: {e}")
        clarification_question = f"Could you share your {', '.join(missing_info)}?"
    return {"messages": state["messages"] + [clarification_question]}