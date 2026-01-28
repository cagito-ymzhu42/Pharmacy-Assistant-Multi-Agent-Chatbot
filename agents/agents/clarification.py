from typing import Dict, Any
from core.models import AgentState
from core.config import llm

def clarification_agent(state: AgentState) -> Dict[str, Any]:
    """当用户画像信息不完整时，生成针对性的问题进行追问。"""
    print("--- [Agent] 澄清 Agent 正在工作 ---")
    profile = state.get("profile", {})
    
    missing_info = []
    if not profile.get("age"): missing_info.append("年龄")
    if not profile.get("condition"): missing_info.append("具体病情或症状")
    if not profile.get("health_background"): missing_info.append("基础病状或特殊身体状况（例如高血压、怀孕、过敏史等）")
    
    if not missing_info:
        return {"messages": state["messages"] + ["我好像有点混乱，能请您再说一次您的需求吗？"]}

    prompt = f"""你是一个友善且严谨的香港药房导购。为了给用户提供安全准确的建议，你需要询问一些缺失的关键信息。
        请根据以下需要补充的信息，生成一句自然的、口语化的粤语或书面语混合的问句。
        需要补充的信息: {', '.join(missing_info)}
        # 优秀提问范例:
        - 如果缺失 [年龄, 基础病状]: "唔该，为咗更准确推荐，可唔可以话我知你大概几多岁，同埋有冇咩长期病患或者特别身体状况（好似高血压、怀孕咁）？"
        - 如果只缺失 [基础病状]: "为咗确保用药安全，想问下你有冇咩长期病患、过敏史，或者系咪怀孕/哺乳期？如果冇嘅话，可以直接话我知冇。"
        请直接生成最适合当前场景的一句问话，不要包含任何多余的解释。
        """
    
    try:
        clarification_question = llm.invoke(prompt).content.strip()
    except Exception as e:
        print(f"生成澄清问题失败: {e}")
        clarification_question = f"唔好意思，为咗更好咁帮到你，可唔可以提供下你嘅{'、'.join(missing_info)}？"
    return {"messages": state["messages"] + [clarification_question]}