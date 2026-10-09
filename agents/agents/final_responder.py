from typing import Dict, Any
from langchain_core.messages import AIMessage, ToolCall

from core.models import AgentState
from core.catalog import canonical_district, canonical_drug_name

def final_responder(state: AgentState) -> Dict[str, Any]:
    """
    (最终版) 综合所有信息，决定下一步行动。
    - 如果检查者否决，则使用其结论拒绝推荐，并结束会话。
    - 如果检查通过但缺少地区，则使用积极结论追问地区，会话继续。
    - 如果检查通过且地区已知，则直接构造工具调用查询库存，会话继续。
    """
    print("--- [Agent] 综合 Agent 正在工作 ---")
    profile = state["profile"]
    candidates = state["candidates"]
    feedback = state.get("checker_feedback")

    # 路径 1: 检查者“一票否决”。这是最高优先级的判断。
    if not feedback or not feedback.get("is_safe", False):
        rejection_conclusion = feedback.get("conclusion", "Please consult a pharmacist or doctor to review your options.") if feedback else "The review could not be completed. Please consult a pharmacist or doctor."
        print(f"--- [综合 Agent] 方案被否决。理由: {rejection_conclusion} ---")
        return {
            "messages": state["messages"] + [rejection_conclusion], 
            "session_complete": True
        }

    print("--- [综合 Agent] 检查通过，准备下一步。 ---")
    
    if not candidates:
        return {
            "messages": state["messages"] + ["I could not identify a suitable product in the references. A pharmacist can help review your options."],
            "session_complete": True
        }
        
    # 路径 2: 缺少地区信息，需要追问。
    district = canonical_district(profile.get("region") or "")
    if not district:
        drug_names = "、".join([c['drug_name'] for c in candidates])
        positive_conclusion = feedback.get("conclusion", f"The reference search identified {drug_names}.")
        ask_location_prompt = f"{positive_conclusion} Which area should I search: Hong Kong Island, Kowloon, or the New Territories?"
        return {"messages": state["messages"] + [ask_location_prompt]}
        
    # ==============================================================================
    # 路径 3: (核心修改) 所有信息齐全，直接构造工具调用，避免逻辑重复。
    # ==============================================================================
    drug_to_check = canonical_drug_name(candidates[0]['drug_name'])
    district_to_check = district
    
    print(f"--- [综合 Agent] 方案检查通过，直接为 '{drug_to_check}' 在 '{district_to_check}' 构造工具调用 ---")
    
    # 1. 直接构造 ToolCall 对象，明确指定工具名称和参数
    tool_call = ToolCall(
        name="check_nearby_pharmacy_stock",
        args={
            "drug_name": drug_to_check,
            "district": district_to_check
        },
        id="tool_call_direct_1" # id 可以是任意唯一字符串
    )
    
    # 2. 将 ToolCall 包装在 AIMessage 中。这是 LangGraph 的标准格式。
    tool_call_message = AIMessage(content="", tool_calls=[tool_call])
    
    # 3. 将此包含工具调用的消息添加到状态中。
    #    后续的路由节点 (route_after_final_responder) 会检测到这个 tool_calls，
    #    并自动将流程导向 tool_node。
    return {"messages": state["messages"] + [tool_call_message]}