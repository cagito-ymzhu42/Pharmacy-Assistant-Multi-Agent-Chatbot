import json
from typing import Dict, Any

from core.models import AgentState
from core.config import llm

def final_response_generator(state: AgentState) -> Dict[str, Any]:
    """
    (最终版) 在成功查询库存后，综合所有信息生成最终的、完整的回复。
    同时，设置 session_complete 标志，表示本次查询流程已结束。
    """
    print("--- [Generator] 正在生成包含库存信息的最终回复 ---")
    candidates = state["candidates"]
    feedback = state["checker_feedback"]
    
    # 从消息历史中提取最新的工具输出结果
    tool_output = ""
    # 从后往前找，找到最新的 ToolMessage
    for msg in reversed(state['messages']):
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            # 这是工具调用的请求，跳过
            continue
        if hasattr(msg, 'content') and not hasattr(msg, 'tool_calls'):
            # 找到工具的返回结果（它没有 tool_calls 属性）
            # 假设工具返回的消息是最后一条非请求消息
            tool_output = msg.content
            break

    # 构建一个详细的 Prompt，指导 LLM 如何整合所有信息
    prompt = f"""你是一个专业、友善的香港药房导购。请根据以下所有信息，为用户生成一段最终的、完整的、清晰的回复。

# 1. 药师的最终审查结论 (这是回复的开场白和基调):
{json.dumps(feedback.get('conclusion', '药品推荐已通过安全审查。'), ensure_ascii=False)}

# 2. 具体推荐的药品方案 (如果结论是积极的):
{json.dumps(candidates, ensure_ascii=False, indent=2)}

# 3. 库存查询结果:
{tool_output}

# 你的任务:
请将以上所有信息整合成一段通顺流畅的对话。
1.  以药师的审查结论作为开头，让用户感到放心。
2.  接着，自然地列出推荐的药品名称和推荐理由。
3.  最后，附上详细的库存查询结果。
4.  在结尾处，务必加上一句温馨提示，例如“建议您去之前最好先致电药房确认一下库存，以免白行一趟。”

Write the final response in English. Keep Chinese product names alongside any English names. Clearly label the stock results as simulated inventory and recommend contacting the store for current availability. Do not claim a clinical diagnosis or guarantee product safety.
"""
    
    # 调用 LLM 生成最终回复
    final_response = llm.invoke(prompt).content.strip()
    
    # 返回更新后的状态，包括最终回复和会话完成标志
    return {
        "messages": state["messages"] + [final_response], 
        "session_complete": True  # 关键：设置会话完成标志，以便主循环重置状态
    }