"""Shared names for the existing drug graph and regional stock tool."""

DRUG_ALIASES = {
    "必理痛": ("必理痛", "panadol"),
    "幸福伤风素": ("幸福伤风素", "幸福傷風素", "fortune cold"),
    "保济丸": ("保济丸", "保濟丸", "po chai"),
    "双飞人": ("双飞人", "雙飛人", "ricqles", "ricqlès"),
    "无比滴": ("无比滴", "無比滴", "muhi"),
    "撒隆巴斯": ("撒隆巴斯", "萨隆巴斯", "撒隆巴斯止痛贴", "萨隆巴斯止痛贴", "salonpas"),
    "黄道益活络油": ("黄道益", "黃道益", "黄道益活络油", "黃道益活絡油", "wong to yick"),
}
DISTRICT_ALIASES = {
    "港岛": ("港岛", "港島", "hong kong island", "central", "中环", "中環", "causeway bay", "铜锣湾", "銅鑼灣", "north point", "北角"),
    "九龙": ("九龙", "九龍", "kowloon", "mong kok", "旺角", "tsim sha tsui", "尖沙咀", "观塘", "觀塘", "kwun tong"),
    "新界": ("新界", "new territories", "sha tin", "shatin", "沙田", "tuen mun", "屯门", "屯門", "荃湾", "荃灣", "tsuen wan", "元朗", "yuen long", "将军澳", "將軍澳", "tseung kwan o"),
}


def canonical_drug_name(name):
    normalized = name.strip().casefold()
    for canonical, aliases in DRUG_ALIASES.items():
        if normalized == canonical.casefold() or normalized in [alias.casefold() for alias in aliases]:
            return canonical
    return name.strip()


def canonical_district(name):
    normalized = name.strip().casefold()
    for canonical, aliases in DISTRICT_ALIASES.items():
        if any(alias.casefold() in normalized for alias in aliases):
            return canonical
    return None
