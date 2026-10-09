from langchain_community.graphs import Neo4jGraph

def setup_knowledge_graph_with_wongtoyick(graph: Neo4jGraph):
    """
    使用直接执行 Cypher 查询的方式，构建并填充包含“黄道益活络油”的知识图谱。
    """
    print("--- 正在构建包含“黄道益活络油”的香港本地化知识图谱... ---")
    
    # MERGE makes repeated imports reuse the project records.

    # --- 步骤 1: 定义所有数据 (已更新) ---
    # 实体数据
    drugs = ["必理痛", "幸福伤风素", "保济丸", "双飞人", "无比滴", "撒隆巴斯", "黄道益活络油"]
    symptoms = [
        "发烧", "头痛", "肌肉酸痛", "作感冒", "咳嗽", "肚痾", "肠胃不适", 
        "蚊叮虫咬", "皮肤痕痒", "关节痛", "头晕身㷫", "跌打扭伤"
    ]
    populations = [
        "儿童", "成人", "高血压患者", "孕妇", "婴儿", "长者", 
        "哺乳期妇女", "肝病患者", "肾病患者", "心脏病患者", 
        "哮喘患者", "G6PD缺乏症患者"
    ]
    
    # 关系数据
    treats_relations_data = [
        ("必理痛", "发烧"), ("必理痛", "头痛"), ("必理痛", "肌肉酸痛"),
        ("幸福伤风素", "作感冒"), ("幸福伤风素", "头痛"), ("幸福伤风素", "发烧"),
        ("保济丸", "肚痾"), ("保济丸", "肠胃不适"),
        ("双飞人", "头晕身㷫"),
        ("无比滴", "蚊叮虫咬"), ("无比滴", "皮肤痕痒"),
        ("撒隆巴斯", "关节痛"), ("撒隆巴斯", "肌肉酸痛"),
        ("黄道益活络油", "肌肉酸痛"),
        ("黄道益活络油", "关节痛"),
        ("黄道益活络油", "跌打扭伤")
    ]
    
    cautions_data = [
        ("幸福伤风素", "高血压患者", "含有去氧肾上腺素等血管收缩剂，可能导致血压升高，请咨询医生。"),
        ("必理痛", "孕妇", "虽然相对安全，但任何孕期用药前均应咨询医生意见。"),
        ("必理痛", "肝病患者", "主要经肝脏代谢，肝功能不全者需在医生指导下使用，避免过量导致肝损伤。"),
        ("必理痛", "儿童", "需根据体重或年龄使用儿童专用剂型和剂量，切勿过量。"),
        ("必理痛", "肾病患者", "严重肾功能不全者可能需要调整剂量，请咨询医生。"),
        ("幸福伤风素", "心脏病患者", "含有的血管收缩剂成分可能加重心脏负担，请勿自行服用。"),
        ("幸福伤风素", "儿童", "复合感冒药成分复杂，部分成分不适用于幼儿，请选用儿童专用感冒药。"),
        ("幸福伤风素", "哺乳期妇女", "药物成分可能进入母乳，影响婴儿，不建议使用。"),
        ("保济丸", "孕妇", "孕期用药需格外谨慎，请先咨询中医师或医生意见。"),
        ("保济丸", "婴儿", "婴儿肠胃功能脆弱，且对某些中药成分敏感，请在医师指导下使用。"),
        ("双飞人", "婴儿", "含有高浓度酒精和薄荷，对婴儿刺激性强，禁止内服，外用亦需极度谨慎。"),
        ("双飞人", "孕妇", "因含酒精成分，严禁内服。"),
        ("双飞人", "G6PD缺乏症患者", "含有薄荷醇等成分，可能诱发溶血反应，应避免使用。"),
        ("撒隆巴斯", "哮喘患者", "部分哮喘患者对水杨酸盐（阿司匹林类）敏感，可能诱发哮喘，需小心使用。"),
        ("撒隆巴斯", "儿童", "儿童皮肤较薄，易产生刺激或过量吸收，请勿用于12岁以下儿童，或遵医嘱。"),
        ("撒隆巴斯", "孕妇", "孕晚期应避免使用，其他孕期请咨询医生。"),
        ("黄道益活络油", "孕妇", "含有水杨酸甲酯等成分，可能经皮肤吸收，孕期使用前请务必咨询医生。"),
        ("黄道益活络油", "哺乳期妇女", "药物成分可能经皮肤吸收并进入母乳，不建议使用。"),
        ("黄道益活络油", "婴儿", "严禁使用。其成分如樟脑、薄荷醇对婴儿皮肤和神经系统有风险。"),
        ("黄道益活络油", "儿童", "成分对儿童皮肤刺激性较强，请勿大面积使用，并避免用于2岁以下幼儿。"),
        ("黄道益活络油", "G6PD缺乏症患者", "含有樟脑（Camphor），可能诱发溶血反应，应避免使用。"),
        ("黄道益活络油", "哮喘患者", "含有水杨酸甲酯（类似阿司匹林），可能诱发对水杨酸盐敏感的哮喘患者发作。")
    ]

    # --- 步骤 2: 循环执行 Cypher 查询以创建节点 ---
    print("正在创建节点 (Drugs, Symptoms, Populations)...")
    for name in drugs:
        graph.query("MERGE (:Drug {name: $name})", params={"name": name})
    for name in symptoms:
        graph.query("MERGE (:Symptom {name: $name})", params={"name": name})
    for name in populations:
        graph.query("MERGE (:Population {name: $name})", params={"name": name})
    
    # --- 步骤 3: 循环执行 Cypher 查询以创建关系 ---
    print("正在创建关系 (TREATS, REQUIRES_CAUTION_IN)...")
    for drug, symptom in treats_relations_data:
        graph.query(
            "MATCH (d:Drug {name: $d}), (s:Symptom {name: $s}) MERGE (d)-[:TREATS]->(s)",
            params={"d": drug, "s": symptom}
        )
    
    for drug, population, reason in cautions_data:
        graph.query(
            """
            MATCH (d:Drug {name: $d}), (p:Population {name: $p})
            MERGE (d)-[r:REQUIRES_CAUTION_IN]->(p)
            SET r.reason = $reason
            """,
            params={"d": drug, "p": population, "reason": reason}
        )
    
    print("--- 香港本地化知识图谱构建完成 ---")

# --- 执行函数并验证 ---
if __name__ == "__main__":
    import os
    from pathlib import Path
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    graph = Neo4jGraph(
        url=os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687"),
        username=os.getenv("NEO4J_USER", "neo4j"),
        password=os.environ["NEO4J_PASSWORD"],
    )
    # 调用函数来构建图谱
    setup_knowledge_graph_with_wongtoyick(graph)
    
    # 验证“黄道益活络油”是否已成功添加
    print("\n--- 验证“黄道益活络油”相关数据 ---")
    wongtoyick_treats = graph.query("""
    MATCH (:Drug {name: '黄道益活络油'})-[:TREATS]->(s:Symptom)
    RETURN s.name AS symptom
    """)
    wongtoyick_cautions = graph.query("""
    MATCH (:Drug {name: '黄道益活络油'})-[r:REQUIRES_CAUTION_IN]->(p:Population)
    RETURN p.name AS population, r.reason AS reason
    """)
    
    print("黄道益活络油可治疗的症状:")
    for item in wongtoyick_treats:
        print(f"  - {item['symptom']}")
        
    print("\n黄道益活络油的注意事项:")
    for item in wongtoyick_cautions:
        print(f"  - 人群: {item['population']}, 原因: {item['reason']}")