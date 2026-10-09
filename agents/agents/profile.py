from typing import Dict, Any
from langchain_core.output_parsers import PydanticOutputParser

from core.models import AgentState, UserProfile
from core.config import llm
from core.catalog import canonical_district

def profile_agent(state: AgentState) -> Dict[str, Any]:
    """从对话历史中提取或更新用户画像。"""
    print("--- [Agent] 画像 Agent 正在工作 ---")
    previous = state.get("profile", {})
    profile = dict(previous)
    prompt = f"""你是一个香港的药房导购，请从以下整个对话历史中提取或更新完整的用户画像（年龄、病情、健康背景、地区）。
        对话历史: {state['messages']}
        当前已知信息: {profile}
        Use English for symptoms and health background. Preserve existing field wording when the information has not changed. Extract only facts the user supplied.
        {PydanticOutputParser(pydantic_object=UserProfile).get_format_instructions()}"""
    
    try:
        response = llm.invoke(prompt)
        extracted_profile = PydanticOutputParser(pydantic_object=UserProfile).parse(response.content)
        profile.update(extracted_profile.model_dump(exclude_none=True))
        if profile.get("region"):
            profile["region"] = canonical_district(profile["region"])
        print(f"--- 画像更新为: {profile} ---")
    except Exception as e:
        print(f"用户画像提取失败: {e}")
        
    update = {"profile": profile}
    if any(profile.get(key) != previous.get(key) for key in ("age", "condition", "health_background")):
        update.update(candidates=[], checker_feedback=None)
    return update
