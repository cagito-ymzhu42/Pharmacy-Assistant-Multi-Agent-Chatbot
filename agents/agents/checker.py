import json
from typing import Dict, Any
from langchain_core.output_parsers import PydanticOutputParser

from core.models import AgentState, CheckerFeedback
from core.config import llm, graph

def checker_agent(state: AgentState) -> Dict[str, Any]:
    """
    审查推荐方案的合理性和风险。
    它会使用 LLM 进行实体链接（健康背景和年龄组），并使用知识图谱进行深度检查，
    最后由 LLM 进行综合评估。
    """
    print("--- [Agent] 检查者 Agent 正在工作 ---")
    profile = state["profile"]
    candidates = state["candidates"]
    
    # 如果没有初步推荐，则无需检查
    if not candidates:
        return {"checker_feedback": {"is_safe": True, "risks": ["由于没有初步推荐，无需检查。"]}}
    
    # 如果知识图谱未连接，则跳过深度检查，并给出警告
    if not graph:
        print("警告：Neo4j 未连接，跳过知识图谱检查。")
        return {"checker_feedback": {"is_safe": True, "risks": ["知识图谱未连接，无法进行深度检查。"]}}

    # --------------------------------------------------
    # 步骤 1: 实体链接与用户画像标准化
    # --------------------------------------------------
    print("--- [Checker] 步骤 1: 标准化用户画像 ---")
    
    # 从知识图谱获取所有已知的人群/状况节点作为标准列表
    try:
        standard_populations = [p['name'] for p in graph.query("MATCH (p:Population) RETURN p.name as name")]
    except Exception as e:
        print(f"从知识图谱获取人群列表失败: {e}")
        standard_populations = []

    # 1.1 标准化健康背景
    user_health_background = profile.get("health_background", "")
    normalized_backgrounds = [] # 允许多个健康背景
    if user_health_background and standard_populations:
        norm_bg_prompt = f"""
        你是一个医疗术语标准化助手。请从用户的健康背景描述中，提取出所有相关的健康状况，
        并将每一个状况都映射到以下标准术语列表中最接近的一项。
        
        用户健康背景描述: '{user_health_background}'
        标准术语列表: {standard_populations}
        
        请以JSON列表的格式返回所有匹配到的标准术语。例如：["高血压患者", "肝病患者"]。
        如果找不到任何匹配，请返回一个空列表 []。
        """
        try:
            response = llm.invoke(norm_bg_prompt).content.strip()
            parsed_list = json.loads(response)
            if isinstance(parsed_list, list):
                normalized_backgrounds = [term for term in parsed_list if term in standard_populations]
        except (json.JSONDecodeError, TypeError) as e:
            print(f"解析健康背景标准化结果失败: {e}")
            
    if normalized_backgrounds:
        print(f"--- 健康背景标准化: '{user_health_background}' -> {normalized_backgrounds} ---")

    # 1.2 使用 LLM 判断年龄组并严格映射
    user_age_groups = []
    user_age_str = profile.get("age", "")
    if user_age_str and standard_populations:
        age_related_populations = [p for p in standard_populations if p in ["婴儿", "儿童", "青少年", "成人", "长者"]]
        
        age_map_prompt = f"""
        你是一个年龄分段专家。请根据用户的年龄描述，将其映射到一个或多个最合适的年龄分组。
        
        用户年龄描述: '{user_age_str}'
        可选的年龄分组 (必须从这里选择): {age_related_populations}
        
        请以JSON列表的格式返回所有匹配到的分组。例如：["儿童"] 或 ["成人"]。
        - '婴儿' 通常指1岁以下。
        - '儿童' 通常指1-12岁。
        - '青少年' 通常指13-18岁。
        - '长者' 通常指65岁以上。
        - 其他情况归为 '成人'。
        如果无法判断，请返回一个空列表 []。
        """
        try:
            response = llm.invoke(age_map_prompt).content.strip()
            parsed_list = json.loads(response)
            if isinstance(parsed_list, list):
                user_age_groups = [term for term in parsed_list if term in age_related_populations]
        except (json.JSONDecodeError, TypeError) as e:
            print(f"解析年龄组标准化结果失败: {e}")

    if user_age_groups:
        print(f"--- 年龄组判断 (LLM): '{user_age_str}' -> {user_age_groups} ---")

    # 合并所有识别出的用户画像标签
    all_user_tags = list(set(normalized_backgrounds + user_age_groups))
    print(f"--- 最终用户画像标签: {all_user_tags} ---")

    # --------------------------------------------------
    # 步骤 2: 从知识图谱查询风险
    # --------------------------------------------------
    print("--- [Checker] 步骤 2: 查询知识图谱风险 ---")
    kg_risks = []
    
    if all_user_tags:
        for drug in candidates:
            drug_name = drug['drug_name']
            
            # 使用 UNWIND 和 IN 来一次性查询所有标签的风险
            cypher_query = """
            UNWIND $user_tags as tag
            MATCH (d:Drug {name: $drug_name})
            MATCH (p:Population {name: tag})
            OPTIONAL MATCH (d)-[r:CONTRAINDICATED_FOR|REQUIRES_CAUTION_IN]->(p)
            WHERE r IS NOT NULL
            RETURN p.name as population, r.reason as risk
            """
            
            try:
                results = graph.query(cypher_query, params={
                    "drug_name": drug_name,
                    "user_tags": all_user_tags
                })
                for res in results:
                    if res['risk']:
                        risk_desc = f"药品'{drug_name}'对'{res['population']}'存在风险: {res['risk']}"
                        kg_risks.append(risk_desc)
            except Exception as e:
                print(f"知识图谱查询失败: {e}")

    kg_risks = list(set(kg_risks)) # 去重
    print(f"--- 知识图谱查询到 {len(kg_risks)} 条风险 ---")

    # --------------------------------------------------
    # 步骤 3: 使用 LLM 进行综合评估
    # --------------------------------------------------
    print("--- [Checker] 步骤 3: LLM 综合评估 ---")
    output_parser = PydanticOutputParser(pydantic_object=CheckerFeedback)
    format_instructions = output_parser.get_format_instructions()
    kg_risks_str = "\n".join(kg_risks) if kg_risks else "无"

    # --- 这是需要修改的 Prompt ---
    prompt = f"""
你是一个极其严谨、以安全为第一要务的药师审查员。请根据以下所有信息，对一份药品推荐方案进行全面的安全性评估，并生成一段可直接面向用户的结论。

# 1. 完整的用户画像:
{profile}

# 2. 初步推荐的药品方案:
{[drug['drug_name'] for drug in candidates]}

# 3. 从知识图谱中查到的明确风险 (硬性约束):
{kg_risks_str}

# 你的审查任务:
1.  **核心判断 (`is_safe`)**: 结合所有信息，特别是知识图谱的硬性风险，判断方案是否安全。只要存在任何一条知识图谱风险，或你认为有其他重大安全隐患，`is_safe` 就必须是 `false`。
2.  **风险罗列 (`risks`)**: 清晰地列出所有识别出的风险点。这应该包括知识图谱的发现，以及你基于常识判断出的其他潜在风险（例如，即使知识图谱没有数据，但给儿童推荐成人剂量药物也是风险）。
3.  **生成最终结论 (`conclusion`)**: 这是最重要的部分。请撰写一段专业、清晰的结论性文字，这段文字未来会展示给用户。
    - **如果 `is_safe` 为 `false`**: 你的结论应该友善但坚定地解释为什么不能推荐药物，点出核心风险（例如“由于您提到的‘严重发烧’情况复杂，自行用药可能延误病情”），并强烈建议用户“尽快咨询医生进行详细诊断”。【不要】在结论中提具体的药名。
    - **如果 `is_safe` 为 `true`**: 你的结论应该是一段积极的总结，并且【必须明确提及推荐的药品名称】。例如：“根据您提供的信息，您的情况比较清晰，初步为您推荐的‘幸福伤风素’和‘必理痛’是适合且安全的，可以帮助缓解您的症状。”

# 格式要求:
必须严格按照下面的JSON格式输出你的审查结论。
{format_instructions}
"""
    # --- Prompt 修改结束 ---

    try:
        response = llm.invoke(prompt)
        parsed_feedback = output_parser.parse(response.content)
        print(f"--- 检查者反馈: {parsed_feedback.model_dump_json(indent=2, ensure_ascii=False)} ---") # 使用 model_dump_json 更规范
        return {"checker_feedback": parsed_feedback.model_dump()} # 使用 model_dump() 替代 dict()
    except Exception as e:
        print(f"检查者 Agent 综合评估失败: {e}")
        # 如果评估过程出错，出于安全考虑，默认方案为不安全
        return {"checker_feedback": {
            "is_safe": False, 
            "risks": ["审查过程中发生内部错误，建议谨慎对待此推荐。"],
            "conclusion": "抱歉，内部系统在进行安全审查时遇到问题。为确保您的安全，我们暂时无法提供药品建议，强烈建议您咨询专业医生。"
        }}
