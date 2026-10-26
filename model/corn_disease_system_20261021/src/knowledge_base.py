"""玉米病害专业知识库（4 类）。

内容面向田间实际防治常识，供前端"知识库"模块与后端 /knowledge 接口使用。
每个类别包含：症状、发生规律、防治方法（农业防治 / 药剂防治 / 田间管理）。

药剂部分用结构化字段 `prescription` 描述（施药窗口 / 药剂清单 / 重点部位 /
间隔频次 / 注意事项），`control["chemical"]` 的三条要点由它自动生成，
避免"时机句被当成药剂名"这类字段错位。
"""
from __future__ import annotations

import copy
from typing import Any, Dict, List

KNOWLEDGE_BASE: Dict[str, Dict[str, Any]] = {
    "Blight": {
        "name_cn": "玉米大斑病",
        "name_en": "Northern Corn Leaf Blight",
        "pathogen": "真菌，大斑凸脐蠕孢（Setosphaeria turcica / Exserohilum turcicum）",
        "symptoms": [
            "叶片先出现水渍状青灰色小斑点，随后沿叶脉扩展成梭形（长纺锤形）大斑，长 5~20 cm，宽 1~3 cm。",
            "病斑中央灰褐色至黄褐色，边缘暗褐色，潮湿时病斑表面产生灰黑色霉层（分生孢子梗与孢子）。",
            "多从下部叶片开始发病，自下而上蔓延；严重时病斑汇合连片，叶片枯死，形似火烤。",
            "苗期至成株期均可发病，抽雄前后为显症高峰，抗病品种病斑呈褪绿条状而非典型梭形。",
        ],
        "occurrence": [
            "发病条件：日均温 20~25 ℃、相对湿度 90% 以上、连续阴雨或夜间结露时间长时最易流行。",
            "菌源：以菌丝体或分生孢子在病残体上越冬，也可随种子、秸秆传播，是次年主要初侵染源。",
            "传播方式：分生孢子借气流、雨水飞溅远距离传播，一个生长季可多次再侵染。",
            "高发季节：北方春玉米区 7—8 月（抽雄至灌浆期），南方夏玉米区 6—7 月；连作地块、密植郁闭、偏施氮肥田块发病重。",
        ],
        "prescription": {
            "timing": "发病初期（病株率 10%~15%）",
            "drugs": [
                "18.7% 丙环唑·嘧菌酯悬浮剂 1000 倍液",
                "25% 吡唑醚菌酯乳油 1500~2000 倍液",
                "75% 肟菌酯·戊唑醇水分散粒剂 3000 倍液",
                "70% 甲基硫菌灵可湿性粉剂 800 倍液",
            ],
            "focus": "重点喷施中下部叶片",
            "interval": "每隔 7~10 天喷 1 次，连喷 2~3 次，注意轮换用药延缓抗药性",
            "caution": "采收前 20 天停止用药",
        },
        "control": {
            "agricultural": [
                "选用抗病品种（如中抗以上的紧凑型杂交种），这是最经济有效的措施。",
                "实行 2~3 年轮作，避免玉米连作；收获后彻底清除田间病残体，深翻压埋或集中堆沤腐熟。",
                "合理密植，改善行间通风透光；平衡施肥，控氮增磷钾，避免后期脱肥早衰。",
            ],
            "field": [
                "及时摘除底部病叶并带出田外销毁，减少再侵染菌源。",
                "雨后及时排水，降低田间湿度；避免大水漫灌。",
                "抽雄前后是防治关键窗口期，遇连阴雨应提前预防性施药。",
            ],
        },
        "severity": "中高（一般年份减产 10%~20%，流行年份可达 30%~50%）",
    },
    "Common_Rust": {
        "name_cn": "玉米普通锈病",
        "name_en": "Common Corn Rust",
        "pathogen": "真菌，玉米柄锈菌（Puccinia sorghi）",
        "symptoms": [
            "叶片正反两面散生或密生圆形至椭圆形的夏孢子堆，长 0.5~2 mm，隆起，表皮破裂后散出铁锈色（橙红色至黄褐色）粉末。",
            "孢子堆周围常有黄色晕圈；后期孢子堆变黑褐色，产生冬孢子。",
            "多从中上部叶片开始显症，严重时病斑布满整个叶面，叶片提前枯黄、干枯，影响灌浆。",
            "苞叶、叶鞘上也可发生；与南方锈病区别：普通锈病孢子堆色浅偏黄褐、较小，多发生于偏凉爽地区。",
        ],
        "occurrence": [
            "发病条件：日均温 16~23 ℃、高湿、叶面结露或水膜是孢子萌发侵染的必要条件。",
            "菌源：南方温暖地区菌源随西南季风气流远程传播，可通过转主寄主（酢酱草）越冬。",
            "传播方式：夏孢子借气流远距离传播，侵染周期短（约 7~10 天一遍），可多次再侵染。",
            "高发季节：北方玉米区 7—8 月，南方 5—6 月及 9—10 月；山区、昼夜温差大、露水重的田块发病重。",
        ],
        "prescription": {
            "timing": "发病初期（病叶率 5%~10%）",
            "drugs": [
                "25% 三唑酮可湿性粉剂 1000~1500 倍液",
                "12.5% 烯唑醇可湿性粉剂 2000 倍液",
                "25% 吡唑醚菌酯乳油 1500 倍液",
                "43% 戊唑醇悬浮剂 3000 倍液",
            ],
            "focus": "重点保护功能叶",
            "interval": "7~10 天喷 1 次，连续 2 次",
            "caution": "三唑类药剂在高温干旱时慎用，避免药害抑制生长",
        },
        "control": {
            "agricultural": [
                "种植抗锈病品种，注意品种抗性随锈菌小种变异可能丧失，需逐年关注。",
                "合理密植，避免过施氮肥造成叶片肥厚徒长、田间郁闭。",
                "清除田间杂草与自生苗，减少桥梁寄主。",
            ],
            "field": [
                "抽雄期前后巡查田块，及时清理底部重病叶。",
                "与南方菌源区同步监测，气象预报有持续低温高湿时应提前预防。",
                "收获后深翻灭茬，减少越冬菌源。",
            ],
        },
        "severity": "中（一般减产 5%~15%，严重流行时达 30% 以上）",
    },
    "Gray_Leaf_Spot": {
        "name_cn": "玉米灰斑病",
        "name_en": "Gray Leaf Spot",
        "pathogen": "真菌，玉蜀黍尾孢（Cercospora zeae-maydis）",
        "symptoms": [
            "叶片上出现狭长矩形（长条状）病斑，长 1~6 cm，宽 0.2~0.4 cm，病斑受叶脉限制，边缘平直。",
            "病斑中央灰白色至浅褐色，边缘褐色，后期两面产生灰色霉层（分生孢子）。",
            "多从下部叶片向上扩展，严重时病斑连片，叶片枯死呈灰白色，远看如被灰布覆盖。",
            "在湿度大时病斑两端可出现晕圈；与弯孢菌叶斑病区别：后者病斑多卵圆形、有同心轮纹。",
        ],
        "occurrence": [
            "发病条件：温暖高湿最关键，日均温 25~28 ℃、相对湿度 90% 以上、连续阴雨或大雾天气利于流行。",
            "菌源：病菌在病残体（秸秆）上越冬，是主要的初侵染源，种子也可带菌。",
            "传播方式：分生孢子借风雨、气流传至新叶，田间可多次再侵染。",
            "高发季节：华北、东北夏秋多雨年份 7 月下旬—8 月为流行高峰；免耕秸秆还田田块发病重。",
        ],
        "prescription": {
            "timing": "玉米抽雄前后（病叶率 10% 左右）",
            "drugs": [
                "25% 吡唑醚菌酯乳油 1500~2000 倍液",
                "18.7% 丙环唑·嘧菌酯悬浮剂 1000 倍液",
                "75% 肟菌酯·戊唑醇水分散粒剂 3000 倍液",
                "50% 异菌脲可湿性粉剂 1000 倍液",
            ],
            "focus": "这是防治关键期，需重点喷透下部叶片",
            "interval": "间隔 7~10 天喷 1 次，连喷 2~3 次",
            "caution": "注意下部叶片喷透，雨后及时补喷",
        },
        "control": {
            "agricultural": [
                "选用抗病品种；病残体是主要菌源，重病田块应换种抗病品种并加强秸秆处理。",
                "秸秆还田的田块应在播前深翻掩埋，或对残体进行堆沤腐熟处理。",
                "与豆类、薯类等非寄主作物轮作 2 年以上。",
            ],
            "field": [
                "及时排涝散墒，改善田间小气候，降低湿度。",
                "合理密植，去除病叶并带出田外。",
                "收获后深耕晒垡，减少残体上的越冬菌量。",
            ],
        },
        "severity": "中高（严重地块减产 20%~40%，秸秆还田连作田块风险最高）",
    },
    "Healthy": {
        "name_cn": "健康叶片",
        "name_en": "Healthy Leaf",
        "pathogen": "无（未检出明显病斑）",
        "symptoms": [
            "叶片整体呈均匀鲜绿至深绿色，叶脉清晰，无坏死斑、锈色孢子堆或灰白长条病斑。",
            "叶面平整有光泽，无明显萎蔫、卷曲、黄化，叶尖叶缘无焦枯。",
            "植株生长势良好，株型整齐，功能叶比例高。",
        ],
        "occurrence": [
            "当前叶片未表现出 MCDD 数据集所涵盖的三种主要叶部病害特征，判定为健康状态。",
            "建议结合田间整体情况观察：单叶健康不代表整株无病，仍需关注下部叶片与茎秆。",
        ],
        "prescription": {
            "timing": "病害高发季节（抽雄前后遇连阴雨）",
            "drugs": [],
            "focus": "无需常规用药",
            "interval": "可喷施代森锰锌等保护性杀菌剂做 1 次预防",
            "caution": "盲目喷杀菌剂会增加成本并可能诱导抗药性",
            "bullets": [
                "无需用药。盲目喷杀菌剂会增加成本并可能诱导抗药性。",
                "可在病害高发季节（抽雄前后遇连阴雨）进行预防性保护施药。",
            ],
        },
        "control": {
            "agricultural": [
                "保持当前水肥管理：平衡施用氮磷钾，避免偏施氮肥。",
                "合理密植、及时中耕除草，保持田间通风透光。",
                "选用抗病品种，坚持轮作与秸秆处理，降低潜在菌源。",
            ],
            "field": [
                "定期巡田（每 5~7 天一次），重点检查下部叶片是否有早期病斑。",
                "雨后及时排水，避免田间积水造成根系缺氧。",
            ],
        },
        "severity": "无（请继续保持良好田间管理）",
    },
}


def _period(text: str) -> str:
    """补足句末标点，避免拼接后出现「。，」这类叠标点。"""
    text = (text or "").strip()
    if not text:
        return ""
    return text if text[-1] in "。！？" else text + "。"


def build_chemical_bullets(rx: Dict[str, Any]) -> List[str]:
    """由结构化处方生成「药剂防治」三条要点（时机 / 药剂 / 频次）。"""
    if not rx:
        return []
    if rx.get("bullets"):
        return list(rx["bullets"])

    bullets: List[str] = []
    timing = (rx.get("timing") or "").strip()
    focus = (rx.get("focus") or "").strip()
    if timing:
        head = f"{timing}开始施药"
        if focus:
            head += f"，{focus}"
        bullets.append(_period(head))

    drugs = [d for d in (rx.get("drugs") or []) if d]
    if drugs:
        bullets.append(f"可选药剂：{'；'.join(drugs)}。")

    tail = "；".join(p for p in [(rx.get("interval") or "").strip(), (rx.get("caution") or "").strip()] if p)
    if tail:
        bullets.append(_period(tail))
    return bullets


# 用结构化处方回填 control["chemical"]，保证「知识库页面」与「决策卡处方」同源
for _entry in KNOWLEDGE_BASE.values():
    _entry.setdefault("control", {})["chemical"] = build_chemical_bullets(_entry.get("prescription") or {})


def get_prescription(class_en_name: str, max_drugs: int = 2) -> Dict[str, Any]:
    """返回结构化处方 + 可直接上屏的文案。

    - drugs_text: 全部药剂（用于知识库/AI 问答）
    - drugs_short: 前 max_drugs 种药剂（用于决策卡单句处方）
    - sentence: 决策卡「选用 …」完整文案（无叠标点）
    """
    kb = get_knowledge(class_en_name)
    rx = dict(kb.get("prescription") or {})
    drugs = [d for d in (rx.get("drugs") or []) if d]
    drugs_short = " 或 ".join(drugs[:max_drugs])
    if drugs:
        timing = (rx.get("timing") or "").strip()
        timing = f"{timing}施药，" if timing else ""
        sentence = f"选用 {drugs_short}，{timing}利用大田植保无人机实施傍晚超低空变量精准喷雾。"
    else:
        sentence = "当前未检出病斑，无需化学防治，保持常规水肥一体化管理并加强田间巡查即可。"
    rx.update(
        {
            "drugs_text": "；".join(drugs),
            "drugs_short": drugs_short,
            "sentence": sentence,
        }
    )
    return rx


def get_knowledge(class_en_name: str) -> Dict[str, Any]:
    """按英文类别名获取知识库内容；未知类别返回兜底结构。"""
    if class_en_name in KNOWLEDGE_BASE:
        return copy.deepcopy(KNOWLEDGE_BASE[class_en_name])
    return {
        "name_cn": class_en_name,
        "name_en": class_en_name,
        "pathogen": "未知",
        "symptoms": ["暂无该类别知识库内容，请补充。"],
        "occurrence": ["暂无该类别知识库内容，请补充。"],
        "prescription": {},
        "control": {"agricultural": [], "chemical": [], "field": []},
        "severity": "未知",
    }


__all__ = ["KNOWLEDGE_BASE", "get_knowledge", "get_prescription", "build_chemical_bullets"]
