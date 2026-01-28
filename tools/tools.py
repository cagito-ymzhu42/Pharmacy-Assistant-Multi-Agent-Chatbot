from langchain_core.tools import tool

@tool
def check_nearby_pharmacy_stock(drug_name: str, district: str) -> str:
    """
    查询香港指定地区屈臣氏药房是否有指定药品的库存。
    - 支持药品名称的模糊匹配（例如 '双飞人药水' 能匹配到 '双飞人'）。
    - 如果指定地区没有，会自动搜索其他地区并返回结果。
    district 参数必须是 '港岛', '九龙', 或 '新界' 之一。
    """
    print(f"--- [工具] 正在为 '{drug_name}' (模糊匹配) 在 '{district}' 区域查询库存... ---")
    
    stock_db = {
        "港岛": {
            "必理痛": ["屈臣氏 (铜锣湾时代广场店)", "屈臣氏 (中环皇后大道中店)", "屈臣氏 (太古城中心店)"],
            "幸福伤风素": ["屈臣氏 (中环皇后大道中店)"],
            "黄道益": ["屈臣氏 (中环皇后大道中店)"],
            "保济丸": ["屈臣氏 (铜锣湾时代广场店)"],
            "双飞人": ["屈臣氏 (太古城中心店)"],
            "无比滴": ["屈臣氏 (中环皇后大道中店)", "屈臣氏 (太古城中心店)"],
            "撒隆巴斯": ["屈臣氏 (铜锣湾时代广场店)", "屈臣氏 (北角汇店)"]
        },
        "九龙": {
            "必理痛": ["屈臣氏 (尖沙咀海港城店)", "屈臣氏 (旺角弥敦道店)", "屈臣氏 (观塘APM店)"],
            "幸福伤风素": ["屈臣氏 (旺角弥敦道店)", "屈臣氏 (观塘APM店)"],
            "保济丸": ["屈臣氏 (黄大仙中心店)"],
            "双飞人": ["屈臣氏 (尖沙咀海港城店)", "屈臣氏 (旺角弥敦道店)"],
            "无比滴": ["屈臣氏 (尖沙咀海港城店)"],
            "撒隆巴斯": ["屈臣氏 (旺角弥敦道店)", "屈臣氏 (观塘APM店)", "屈臣氏 (九龙塘又一城店)"]
        },
        "新界": {
            "必理痛": ["屈臣氏 (沙田新城市广场店)", "屈臣氏 (屯门市广场店)", "屈臣氏 (荃湾广场店)"],
            "幸福伤风素": ["屈臣氏 (沙田新城市广场店)", "屈臣氏 (元朗广场店)"],
            "保济丸": ["屈臣氏 (元朗广场店)"],
            "双飞人": ["屈臣氏 (上水广场店)"],
            "无比滴": ["屈臣氏 (屯门市广场店)"],
            "撒隆巴斯": ["屈臣氏 (沙田新城市广场店)", "屈臣氏 (屯门市广场店)", "屈臣氏 (将军澳PopCorn店)"]
        }
    }
    
    valid_districts = ["港岛", "九龙", "新界"]
    matched_district = next((d for d in valid_districts if d in district), None)
            
    if not matched_district:
        return f"抱歉，请输入有效的区域：港岛、九龙或新界。"

    def find_drug_stock(target_drug: str, district_name: str) -> (str, list):
        district_stock = stock_db.get(district_name, {})
        for db_drug_name, stock_list in district_stock.items():
            if db_drug_name in target_drug or target_drug in db_drug_name:
                return db_drug_name, stock_list
        return None, []

    found_drug_name, stores_in_primary_district = find_drug_stock(drug_name, matched_district)
    
    if stores_in_primary_district:
        return f"在 {matched_district} 区域找到以下屈臣氏药房有 '{found_drug_name}' 的库存: {', '.join(stores_in_primary_district)}。建议您去之前电话确认。"
    else:
        print(f"--- [工具] 在 '{matched_district}' 未找到，开始在其他区域搜索... ---")
        fallback_results = []
        other_districts = [d for d in valid_districts if d != matched_district]
        
        for other_district in other_districts:
            fallback_drug_name, stores_in_other_district = find_drug_stock(drug_name, other_district)
            if stores_in_other_district:
                result_str = f"在 {other_district} 区域({fallback_drug_name}): {', '.join(stores_in_other_district)}"
                fallback_results.append(result_str)
        
        if fallback_results:
            fallback_message = "；".join(fallback_results)
            return (f"抱歉，在 {matched_district} 区域的屈臣氏未能查询到 '{drug_name}' 的库存。"
                    f"不过，在其他区域找到了: {fallback_message}。建议您去之前电话确认。")
        else:
            return f"抱歉，在香港所有区域的屈臣氏都未能查询到 '{drug_name}' 的库存信息。"

# 方便导入
pharmacy_tools = [check_nearby_pharmacy_stock]