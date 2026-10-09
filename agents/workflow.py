from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# 从项目模块中导入
from core.models import AgentState
from core.config import llm
from tools.tools import pharmacy_tools

from .agents import (
    profile_agent,
    clarification_agent,
    recommender_agent,
    checker_agent,
    final_responder,
    final_response_generator
)

def router(state: AgentState) -> str:
    """
    决策下一步走向。
    现在，age, condition, 和 health_background 都被视为必需信息。
    """
    print("--- [Router] 正在决策... ---")
    profile = state.get("profile", {})
    
    # 定义所有必需的用户画像信息
    required_keys = ["age", "condition", "health_background"]
    
    # 检查必需信息是否都已提供
    # 注意：用户可以说“没有”基础病，这也会被提取并视为已提供信息。
    if not all(k in profile and profile[k] for k in required_keys):
        # 如果信息不全，导向澄清节点去追问
        return "clarification_agent"
    
    # 如果还没有初步推荐，则去推荐
    if not state.get("candidates"):
        return "recommender_agent"
    
    # 如果还没有检查，则去检查
    if not state.get("checker_feedback"):
        return "checker_agent"
        
    # 如果以上都有，则进入最终回复阶段
    # 这种情况发生在多轮对话中，例如用户提供了地区信息后，Agent“记住了”之前的推荐和审查结果
    return "final_responder"

def route_after_final_responder(state: AgentState) -> str:
    """
    在 final_responder 节点之后的路由决策。
    它检查 final_responder 的输出，决定下一步是去执行工具还是结束流程。
    """
    # 获取消息列表中的最后一条消息
    last_message = state['messages'][-1]
    
    # 检查最后一条消息是否是一个包含工具调用指令的 AIMessage
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        # 如果是，说明 final_responder 成功生成了工具调用，流程应转向工具节点
        print("--- [Router 2] 检测到工具调用，转向 tool_node ---")
        return "tool_node"
    else:
        # 如果不是，说明 final_responder 生成了最终的文本回复（拒绝或追问）
        # 这种情况下，流程应该结束，等待用户下一次输入
        print("--- [Router 2] 未检测到工具调用，流程结束 ---")
        return END

def create_workflow():
    """创建并编译LangGraph工作流"""
    workflow = StateGraph(AgentState)
    tool_node = ToolNode(pharmacy_tools)

    # 添加所有节点，包括新的澄清节点
    workflow.add_node("profile_agent", profile_agent)
    workflow.add_node("clarification_agent", clarification_agent) # <--- 新增节点
    workflow.add_node("recommender_agent", recommender_agent)
    workflow.add_node("checker_agent", checker_agent)
    workflow.add_node("final_responder", final_responder)
    def run_tools(state):
        update = tool_node.invoke(state)
        return {"messages": state["messages"] + update["messages"]}

    workflow.add_node("tool_node", run_tools)
    workflow.add_node("final_response_generator", final_response_generator)

    workflow.set_entry_point("profile_agent")

    # 定义流程
    workflow.add_conditional_edges(
        "profile_agent",
        router,
        {
            "clarification_agent": "clarification_agent", 
            "recommender_agent": "recommender_agent",
            "checker_agent": "checker_agent",
            "final_responder": "final_responder"
        }
    )

    # 澄清节点执行后，流程结束，等待用户下一次输入
    workflow.add_edge("clarification_agent", END) 

    workflow.add_edge("recommender_agent", "checker_agent")
    workflow.add_edge("checker_agent", "final_responder")

    # final_responder 之后的新路由
    workflow.add_conditional_edges(
        "final_responder",
        route_after_final_responder,
        {
            "tool_node": "tool_node",
            END: END
        }
    )

    # (清理无效代码) 从tool_node出来的边应该指向一个能生成最终回复的节点
    workflow.add_edge("tool_node", "final_response_generator")
    workflow.add_edge("final_response_generator", END)
        
    # 编译工作流
    app = workflow.compile()
    return app

# 创建一个可供全局导入的app实例
app = create_workflow()