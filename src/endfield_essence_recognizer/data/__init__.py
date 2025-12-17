import importlib.resources
import json
from typing import TypedDict


class WeaponStats(TypedDict):
    attribute: str | None
    """基础属性"""
    secondary: str | None
    """附加属性"""
    skill: str | None
    """技能属性"""


class Weapon(TypedDict):
    """已实装武器数据类型"""

    weaponId: str
    """武器 ID"""
    weaponName: str
    """武器名称"""
    weaponType: str
    """武器类型（单手剑 / 双手剑 / 长柄武器 / 手铳 / 施术单元）"""
    rarity: int
    """武器稀有度（3 / 4 / 5）"""
    stats: WeaponStats
    """武器属性数据"""


type Weapons = dict[str, Weapon]


weapons_json_path = (
    importlib.resources.files("endfield_essence_recognizer") / "data" / "weapons.json"
)
weapons: Weapons = json.loads(weapons_json_path.read_text(encoding="utf-8"))
"""已实装武器数据字典"""

all_attribute_stats = ["敏捷提升", "力量提升", "意志提升", "智识提升", "主能力提升"]
all_secondary_stats = [
    "攻击提升",
    "生命提升",
    "物理伤害提升",
    "灼热伤害提升",
    "电磁伤害提升",
    "寒冷伤害提升",
    "自然伤害提升",
    "暴击率提升",
    "源石技艺提升",
    "终结技效率提升",
    "法术伤害提升",
    "治疗效率提升",
]
all_skill_stats = [
    "强攻",
    "压制",
    "追袭",
    "粉碎",
    "昂扬",
    "巧技",
    "残暴",
    "附术",
    "医疗",
    "切骨",
    "迸发",
    "夜幕",
    "流转",
    "效益",
]
