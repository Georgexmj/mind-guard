"""
Import China-localized guidelines/consensus knowledge into rag_knowledge_items.

Usage:
  python -m backend.scripts.import_rag_cn_guidelines
or
  cd backend && python scripts/import_rag_cn_guidelines.py
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.database import SessionLocal  # noqa: E402
from app.models.rag import KnowledgeType, RagKnowledgeItem  # noqa: E402


def _seed_rows() -> List[Dict]:
    now = datetime.utcnow().isoformat()
    return [
        {
            "kb_type": KnowledgeType.rule,
            "title": "国家行动计划目标：到2030年建立痴呆综合连续防控体系",
            "content": (
                "《应对老年期痴呆国家行动计划（2024-2030年）》提出：到2030年基本建立覆盖预防、筛查、"
                "诊疗、康复、照护的综合连续防控体系，并有效控制患病率增速。"
            ),
            "tags": "中国,国家行动计划,政策,体系建设,screening,rule",
            "metadata_json": {
                "rule_id": "CN-R-NHC-PLAN-2030-001",
                "source_org": "国家卫生健康委等15部门",
                "source_type": "national_action_plan",
                "source_title": "应对老年期痴呆国家行动计划（2024-2030年）",
                "source_url": "https://www.nhc.gov.cn/wjw/c100375/202501/521ab3ce974c48a989e0b976ecf8f767.shtml",
                "source_date": "2024-12-31",
                "retrieved_at": now,
                "evidence_level": "national_policy",
                "locale": "zh-CN",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.rule,
            "title": "国家行动计划：65岁及以上人群应推进认知功能初筛与阳性转诊",
            "content": (
                "结合基本公共卫生老年人健康管理，推进65岁及以上老年人认知功能初筛；"
                "对初筛阳性者进一步评估与早期干预，评估异常者应转诊至有条件医疗机构。"
            ),
            "tags": "中国,国家行动计划,65岁+,初筛,转诊,rule",
            "metadata_json": {
                "rule_id": "CN-R-NHC-PLAN-SCREEN-001",
                "source_org": "国家卫生健康委等15部门",
                "source_type": "national_action_plan",
                "source_title": "应对老年期痴呆国家行动计划（2024-2030年）",
                "source_url": "https://www.nhc.gov.cn/wjw/c100375/202501/521ab3ce974c48a989e0b976ecf8f767.shtml",
                "source_date": "2024-12-31",
                "retrieved_at": now,
                "evidence_level": "national_policy",
                "locale": "zh-CN",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.rule,
            "title": "国家行动计划：构建“筛查-诊疗-康复-随访”全病程管理",
            "content": (
                "通过基层与上级医院双向转诊，构建“筛查-诊疗-康复-随访”全病程管理服务体系；"
                "鼓励设立记忆门诊和认知障碍相关专科。"
            ),
            "tags": "中国,国家行动计划,全病程管理,记忆门诊,rule",
            "metadata_json": {
                "rule_id": "CN-R-NHC-PLAN-PATHWAY-001",
                "source_org": "国家卫生健康委等15部门",
                "source_type": "national_action_plan",
                "source_title": "应对老年期痴呆国家行动计划（2024-2030年）",
                "source_url": "https://www.nhc.gov.cn/wjw/c100375/202501/521ab3ce974c48a989e0b976ecf8f767.shtml",
                "source_date": "2024-12-31",
                "retrieved_at": now,
                "evidence_level": "national_policy",
                "locale": "zh-CN",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.rule,
            "title": "促进行动要求：有条件地区每年为65岁及以上居民提供1次认知初筛",
            "content": (
                "《老年痴呆防治促进行动（2023-2025年）》提出，有条件地区可每年为辖区内65岁及以上常住居民"
                "提供1次认知功能初筛，并开展早发现、早干预。"
            ),
            "tags": "中国,促进行动,年度筛查,65岁+,rule",
            "metadata_json": {
                "rule_id": "CN-R-NHC-2023-SCREEN-001",
                "source_org": "国家卫生健康委办公厅",
                "source_type": "official_notice",
                "source_title": "关于开展老年痴呆防治促进行动(2023-2025年)的通知",
                "source_url": "https://www.nhc.gov.cn/lljks/c100158/202306/6a4c7f7a6f0c47cbb609a07e7f78582d.shtml",
                "source_date": "2023-05-26",
                "retrieved_at": now,
                "evidence_level": "national_program",
                "locale": "zh-CN",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.intervention,
            "title": "促进行动建议：初筛风险人群应进行分类干预与认知训练",
            "content": (
                "对认知功能下降高风险人群，在生活方式指导和健康教育基础上实施认知训练；"
                "对疑似痴呆或高风险人群应及时转诊评估。"
            ),
            "tags": "中国,促进行动,认知训练,分类干预,intervention",
            "metadata_json": {
                "code": "CN-I-NHC-2023-TRAINING-001",
                "source_org": "国家卫生健康委办公厅",
                "source_type": "official_notice",
                "source_title": "关于开展老年痴呆防治促进行动(2023-2025年)的通知",
                "source_url": "https://www.nhc.gov.cn/lljks/c100158/202306/6a4c7f7a6f0c47cbb609a07e7f78582d.shtml",
                "source_date": "2023-05-26",
                "retrieved_at": now,
                "evidence_level": "national_program",
                "locale": "zh-CN",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.rule,
            "title": "特色服务方案：基层可使用AD8与简明社区痴呆筛查量表进行评估",
            "content": (
                "基层医疗卫生机构在老年健康管理中，可结合体检使用AD8和简明社区痴呆筛查量表开展认知功能评估，"
                "发现疑似痴呆者建议上级医疗机构就诊。"
            ),
            "tags": "中国,AD8,CSI-D,基层筛查,rule",
            "metadata_json": {
                "rule_id": "CN-R-NHC-2020-AD8-001",
                "source_org": "国家卫生健康委办公厅",
                "source_type": "technical_program",
                "source_title": "探索老年痴呆防治特色服务工作方案（附件）",
                "source_url": "https://www.nhc.gov.cn/jkj/c100063/202009/f61c67f9858f466eb02e1345136b223a.shtml",
                "source_date": "2020-09-11",
                "retrieved_at": now,
                "evidence_level": "technical_spec",
                "locale": "zh-CN",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.intervention,
            "title": "特色服务方案：对MCI人群开展常态化认知训练与年度随访",
            "content": (
                "对诊断为轻度认知障碍（MCI）的老年人，可由社区全科医生组织常态化认知训练，"
                "并在专科指导下每年随访监测认知变化。"
            ),
            "tags": "中国,MCI,社区管理,随访,认知训练,intervention",
            "metadata_json": {
                "code": "CN-I-NHC-2020-MCI-001",
                "source_org": "国家卫生健康委办公厅",
                "source_type": "technical_program",
                "source_title": "探索老年痴呆防治特色服务工作方案（附件）",
                "source_url": "https://www.nhc.gov.cn/jkj/c100063/202009/f61c67f9858f466eb02e1345136b223a.shtml",
                "source_date": "2020-09-11",
                "retrieved_at": now,
                "evidence_level": "technical_spec",
                "locale": "zh-CN",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.intervention,
            "title": "核心信息：建立脑健康生活方式可延缓认知下降",
            "content": (
                "国家卫健委核心信息强调应形成健康生活方式：规律运动、健康饮食、戒烟限酒、"
                "持续学习与社交、保持乐观，减少社会隔离。"
            ),
            "tags": "中国,核心信息,生活方式,一级预防,intervention",
            "metadata_json": {
                "code": "CN-I-NHC-CORE-2019-001",
                "source_org": "国家卫生健康委办公厅",
                "source_type": "official_core_message",
                "source_title": "阿尔茨海默病预防与干预核心信息",
                "source_url": "https://www.nhc.gov.cn/lljks/c100158/201909/c124c2c91fb74701b11d560aba0ad827.shtml",
                "source_date": "2019-09-17",
                "retrieved_at": now,
                "evidence_level": "official_health_education",
                "locale": "zh-CN",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.intervention,
            "title": "核心信息：重点控制中年期与老年期可干预危险因素",
            "content": (
                "重点关注肥胖、高血压、糖尿病、卒中、抑郁、听力损失等危险因素管理，"
                "控制体重、血压、血糖和血脂，强化慢病共管。"
            ),
            "tags": "中国,危险因素,慢病共管,预防,intervention",
            "metadata_json": {
                "code": "CN-I-NHC-CORE-2019-002",
                "source_org": "国家卫生健康委办公厅",
                "source_type": "official_core_message",
                "source_title": "阿尔茨海默病预防与干预核心信息",
                "source_url": "https://www.nhc.gov.cn/lljks/c100158/201909/c124c2c91fb74701b11d560aba0ad827.shtml",
                "source_date": "2019-09-17",
                "retrieved_at": now,
                "evidence_level": "official_health_education",
                "locale": "zh-CN",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.rule,
            "title": "核心信息：出现早期迹象应及时到记忆门诊/相关专科就诊",
            "content": (
                "若出现近期记忆明显下降、熟悉事务处理困难、时间地点混淆、语言表达困难等早期迹象，"
                "建议尽快至老年病科、神经内科、精神心理科或记忆门诊评估。"
            ),
            "tags": "中国,早期迹象,及时就医,转诊,rule",
            "metadata_json": {
                "rule_id": "CN-R-NHC-CORE-2019-001",
                "source_org": "国家卫生健康委办公厅",
                "source_type": "official_core_message",
                "source_title": "阿尔茨海默病预防与干预核心信息",
                "source_url": "https://www.nhc.gov.cn/lljks/c100158/201909/c124c2c91fb74701b11d560aba0ad827.shtml",
                "source_date": "2019-09-17",
                "retrieved_at": now,
                "evidence_level": "official_health_education",
                "locale": "zh-CN",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.rule,
            "title": "医疗安全提示：缺乏高质量证据的创伤性技术不得作为常规治疗",
            "content": (
                "国家卫健委通知指出，“颈深淋巴管/结—静脉吻合术”用于阿尔茨海默病治疗"
                "处于早期探索阶段，安全性和有效性缺乏高质量证据，禁止常规临床应用。"
            ),
            "tags": "中国,医疗安全,证据不足,禁用技术,rule",
            "metadata_json": {
                "rule_id": "CN-R-NHC-SAFETY-2025-001",
                "source_org": "国家卫生健康委办公厅",
                "source_type": "official_notice",
                "source_title": "关于禁止将“颈深淋巴管/结—静脉吻合术”应用于阿尔茨海默病治疗的通知",
                "source_url": "https://www.nhc.gov.cn/yzygj/c100068/202507/a82579bab19a465596b65bf7ef9d3432.shtml",
                "source_date": "2025-06-28",
                "retrieved_at": now,
                "evidence_level": "regulatory_safety_notice",
                "locale": "zh-CN",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.intervention,
            "title": "中国专家共识（2024）：早期预防应覆盖个人-家庭-社会三层策略",
            "content": (
                "《中国阿尔茨海默病早期预防指南（2024）》强调结合中国老年健康和社会文化特点，"
                "从个人、家庭、社会三个层面开展早期预防，包括运动、营养、睡眠、社交和慢病管理。"
            ),
            "tags": "中国,专家共识,早期预防,个人家庭社会,intervention",
            "metadata_json": {
                "code": "CN-I-CAAD-2024-PREVENT-001",
                "source_org": "阿尔茨海默病防治协会（CAAD）",
                "source_type": "expert_consensus",
                "source_title": "中国阿尔茨海默病早期预防指南（2024）",
                "source_url": "https://www.alzcn.com/CN/10.3969/j.issn.2096-5516.2024.03.002",
                "source_date": "2024-07-30",
                "doi": "10.3969/j.issn.2096-5516.2024.03.002",
                "retrieved_at": now,
                "evidence_level": "expert_consensus",
                "locale": "zh-CN",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.rule,
            "title": "中国专家共识（2024）：居家筛查阳性后需进入规范转诊与进一步评估",
            "content": (
                "《阿尔茨海默病居家筛查专家共识》提出，居家筛查适用于早期发现高风险或疑似人群，"
                "但不能替代临床诊断，阳性结果应转入医疗机构做进一步评估。"
            ),
            "tags": "中国,专家共识,居家筛查,转诊,rule",
            "metadata_json": {
                "rule_id": "CN-R-CAAD-2024-HOME-001",
                "source_org": "阿尔茨海默病防治协会（CAAD）",
                "source_type": "expert_consensus",
                "source_title": "阿尔茨海默病居家筛查专家共识",
                "source_url": "https://www.alzcn.com/CN/10.3969/j.issn.2096-5516.2024.03.003",
                "source_date": "2024-07-30",
                "doi": "10.3969/j.issn.2096-5516.2024.03.003",
                "retrieved_at": now,
                "evidence_level": "expert_consensus",
                "locale": "zh-CN",
            },
            "is_active": True,
        },
    ]


def upsert_rows() -> Tuple[int, int]:
    db = SessionLocal()
    created = 0
    updated = 0
    try:
        rows = _seed_rows()
        for row in rows:
            source_url = (row.get("metadata_json") or {}).get("source_url")
            item = (
                db.query(RagKnowledgeItem)
                .filter(RagKnowledgeItem.title == row["title"])
                .first()
            )
            if item is None and source_url:
                item = (
                    db.query(RagKnowledgeItem)
                    .filter(RagKnowledgeItem.metadata_json["source_url"].as_string() == source_url)
                    .first()
                )
            if item is None:
                db.add(RagKnowledgeItem(**row))
                created += 1
            else:
                item.kb_type = row["kb_type"]
                item.title = row["title"]
                item.content = row["content"]
                item.tags = row.get("tags")
                item.metadata_json = row.get("metadata_json")
                item.is_active = bool(row.get("is_active", True))
                updated += 1

        db.commit()
        return created, updated
    finally:
        db.close()


if __name__ == "__main__":
    c, u = upsert_rows()
    print(f"CN guideline import done. created={c}, updated={u}")

