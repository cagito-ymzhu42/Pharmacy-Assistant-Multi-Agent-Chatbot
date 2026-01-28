import json
from typing import Dict, Any
from langchain_core.output_parsers import PydanticOutputParser

from core.models import AgentState, Recommendation
from core.config import llm, vectorstore


def recommender_agent(state: AgentState) -> Dict[str, Any]:
    print("--- [Agent] 推荐 Agent 正在工作 ---")
    profile = state["profile"]
    original_query = profile.get("condition", "")

    # 如果没有病情描述，直接返回空推荐
    if not original_query:
        print("--- [Recommender] 用户画像中未发现病情描述，跳过推荐。 ---")
        return {"candidates": []}

    # ==============================================================================
    # 步骤 0: 查询扩展 (Query Expansion)
    # 将用户的简单症状，通过 LLM 扩展为一段语义丰富的描述，用于向量检索。
    # ==============================================================================
    print(f"--- [Recommender] 步骤 0: 正在为 '{original_query}' 生成语义化查询... ---")
    
    expansion_prompt = f"""
    你是一个医疗知识库的检索专家。你的任务是根据用户的简单症状描述和个人情况，生成一段详细、语义丰富的描述性文本。这段文本将用于在药品说明书向量数据库中进行检索，因此它应该听起来像药品说明书中“适应症”或“功能主治”部分的描述。

    # 用户信息:
    {json.dumps(profile, ensure_ascii=False)}

    # 用户简单症状:
    "{original_query}"

    # 你的任务:
    请生成一段流畅的、用于检索的描述性文本。请直接输出文本，不要包含任何前缀或解释。

    # 优秀范例:
    - 输入症状 "咳嗽": "用于缓解因普通感冒、流感或支气管炎引起的咳嗽、咳痰、喉咙不适等呼吸道症状。"
    - 输入症状 "肌肉酸痛": "适用于缓解因运动拉伤、扭伤、关节炎或过度劳累导致的局部肌肉疼痛、肿胀和酸痛不适。"
    - 输入症状 "头痛发烧": "用于治疗成人和儿童的轻至中度疼痛，如头痛、牙痛、神经痛，并能有效退烧，缓解由普通感冒或流感引起的发热症状。"
    """
    
    try:
        # 使用 LLM 生成语义化查询
        semantic_query = llm.invoke(expansion_prompt).content.strip()
        print(f"--- [Recommender] 生成的语义化查询: '{semantic_query}' ---")
    except Exception as e:
        print(f"--- [Recommender] 查询扩展失败: {e}。将使用原始查询。 ---")
        # 如果扩展失败，回退到使用原始查询，保证流程健壮性
        semantic_query = original_query

    # ==============================================================================
    # 步骤 1: 使用扩展后的查询进行向量检索
    # ==============================================================================
    docs = vectorstore.similarity_search(semantic_query, k=5) if vectorstore else []
    retrieved_docs = [doc.page_content for doc in docs]
    
    print(f"--- [Recommender] 向量数据库为查询 '{semantic_query[:50]}...' 检索到以下内容: ---")
    for i, doc in enumerate(retrieved_docs):
        print(f"  [文档 {i+1}]: {doc[:100]}...")
    print("-----------------------------------------------------------------")
    
    docs_content = "\n---\n".join(retrieved_docs) if retrieved_docs else "无"
    
    # ==============================================================================
    # 步骤 2: 构建推荐 Prompt (保持不变)
    # 这里的 prompt 仍然使用 original_query 来判断相关性，因为这是用户的原始意图。
    # ==============================================================================
    prompt = f"""你是一个专业、严谨的香港药房导购。你的任务是基于用户画像和可能相关的参考文档，生成一个初步的、合理的药品推荐。
# 1. 用户画像:
{profile}
# 2. 检索到的参考文档 (这些文档是基于扩展查询找到的，可能相关，也可能完全不相关):
{docs_content}
# 你的工作流程:
1.  **严格评估文档相关性**: 首先，请仔细判断每一份参考文档是否真的与用户的病情 '{original_query}' 相关。例如，如果用户是伤风，而文档是关于肌肉拉伤的，那么这份文档就是不相关的。
2.  **忽略不相关信息**: 在生成推荐时，你必须【完全忽略】所有不相关的文档内容。
3.  **生成推荐**: 基于用户的画像，并【仅结合相关的参考文档和你自身的专业知识】，生成药品推荐。如果所有文档都不相关，请完全依赖你的专业知识进行推荐。
4.  **格式化输出**: 你的最终输出必须严格遵循以下JSON格式。
{PydanticOutputParser(pydantic_object=Recommendation).get_format_instructions()}"""
    print(prompt)
    
    try:
        response = llm.invoke(prompt)
        print(response.content)  # 打印完整的 LLM 响应以供调试
        parsed_output = PydanticOutputParser(pydantic_object=Recommendation).parse(response.content)
        
        # --- 新增调试日志 ---
        print(f"--- [Recommender] 生成的初步推荐: {[drug.drug_name for drug in parsed_output.recommended_drugs]} ---")
        
        # 使用 model_dump() 替代已弃用的 dict()
        return {"candidates": [drug.model_dump() for drug in parsed_output.recommended_drugs]}
    except Exception as e:
        print(f"初步推荐生成失败: {e}")
        return {"candidates": []}
