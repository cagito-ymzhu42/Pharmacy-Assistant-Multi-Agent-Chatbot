from typing import Dict, Any
from langchain_core.messages import AIMessage, ToolCall

from core.models import AgentState

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
        rejection_conclusion = feedback.get("conclusion", "为确保您的安全，我们暂时无法提供药品建议，强烈建议您咨询专业医生。") if feedback else "内部审查系统出错，为安全起见，建议咨询医生。"
        print(f"--- [综合 Agent] 方案被否决。理由: {rejection_conclusion} ---")
        return {
            "messages": state["messages"] + [rejection_conclusion], 
            "session_complete": True
        }

    print("--- [综合 Agent] 检查通过，准备下一步。 ---")
    
    if not candidates:
        return {
            "messages": state["messages"] + ["根据您提供的信息，我暂时未能找到合适的药品推荐。"],
            "session_complete": True
        }
        
    # 路径 2: 缺少地区信息，需要追问。
    if not profile.get("region"):
        drug_names = "、".join([c['drug_name'] for c in candidates])
        positive_conclusion = feedback.get("conclusion", f"根据您的情况，我初步为您推荐了 {drug_names}。")
        ask_location_prompt = f"{positive_conclusion} 为咗帮你稳附近边间屈臣氏有货，可唔可以话我知你大概喺边区？（例如：港岛、九龙、新界）"
        return {"messages": state["messages"] + [ask_location_prompt]}
        
    # ==============================================================================
    # 路径 3: (核心修改) 所有信息齐全，直接构造工具调用，避免逻辑重复。
    # ==============================================================================
    drug_to_check = candidates[0]['drug_name']
    district_to_check = profile['region']
    
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