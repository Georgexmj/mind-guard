"""
Import web-sourced, traceable RAG knowledge items into rag_knowledge_items.

Usage:
  python -m backend.scripts.import_rag_web_knowledge
or
  cd backend && python scripts/import_rag_web_knowledge.py
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
            "title": "MoCA教育年限校正规则（官方FAQ）",
            "content": (
                "MoCA Full版本在受教育年限≤12年时可加1分，且总分上限仍为30分。"
                "不同版本可能有不同校正规则，必须按对应版本说明执行。"
            ),
            "tags": "moca,education,scoring,rule",
            "metadata_json": {
                "rule_id": "R-MOCA-EDU-WEB-001",
                "source_org": "MoCA Cognition",
                "source_type": "official_faq",
                "source_url": "https://mocacognition.com/faq/",
                "retrieved_at": now,
                "evidence_level": "official_instruction",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.rule,
            "title": "MoCA解释口径应由专业人员执行",
            "content": "MoCA结果解释应由具备认知领域专业能力的医务人员执行，不应作为单次自诊断结论。",
            "tags": "moca,interpretation,safety,rule",
            "metadata_json": {
                "rule_id": "R-MOCA-INTERP-WEB-001",
                "source_org": "MoCA Cognition",
                "source_type": "official_faq",
                "source_url": "https://mocacognition.com/faq/",
                "retrieved_at": now,
                "evidence_level": "official_instruction",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.rule,
            "title": "社区无症状老人普筛证据不足（USPSTF）",
            "content": (
                "对无症状、社区居住的65岁及以上老年人，USPSTF给出I声明："
                "当前证据不足以评估常规筛查认知损害的收益与风险。"
                "临床应保持警觉并在出现早期症状时进行评估。"
            ),
            "tags": "screening,uspstf,primary_care,rule",
            "metadata_json": {
                "rule_id": "R-SCREEN-USPSTF-001",
                "source_org": "USPSTF",
                "source_type": "guideline_recommendation",
                "source_url": "https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/cognitive-impairment-in-older-adults-screening",
                "source_date": "2020-02-25",
                "retrieved_at": now,
                "evidence_level": "guideline",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.rule,
            "title": "量表对MCI识别一致性较弱（USPSTF证据综述）",
            "content": (
                "USPSTF证据综述提示：针对MCI的筛查准确性在不同工具间差异较大，"
                "一致性和精确性不如对痴呆的识别。应结合随访与多源信息综合判断。"
            ),
            "tags": "mci,accuracy,evidence,rule",
            "metadata_json": {
                "rule_id": "R-MCI-ACCURACY-USPSTF-001",
                "source_org": "USPSTF",
                "source_type": "evidence_summary",
                "source_url": "https://www.uspreventiveservicestaskforce.org/uspstf/document/final-evidence-summary/cognitive-impairment-in-older-adults-screening",
                "retrieved_at": now,
                "evidence_level": "systematic_review_summary",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.rule,
            "title": "疑似痴呆应先排除可逆原因（NICE）",
            "content": (
                "当怀疑认知下降时，应先调查可逆原因（如谵妄、抑郁、感官障碍、"
                "抗胆碱负担相关药物等），仍怀疑痴呆再转专科记忆门诊进一步评估。"
            ),
            "tags": "diagnosis,triage,rule,nice",
            "metadata_json": {
                "rule_id": "R-REVERSIBLE-NICE-001",
                "source_org": "NICE",
                "source_type": "guideline",
                "source_url": "https://www.nice.org.uk/guidance/ng97/chapter/Recommendations",
                "retrieved_at": now,
                "evidence_level": "guideline",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.rule,
            "title": "诊断需综合评估而非单一测试（NICE）",
            "content": (
                "专科诊断应基于神经系统检查与认知测试确认认知下降，并在可能时进行亚型诊断；"
                "必要时可加做神经心理评估与结构影像。"
            ),
            "tags": "diagnosis,workflow,nice,rule",
            "metadata_json": {
                "rule_id": "R-DIAG-WORKFLOW-NICE-001",
                "source_org": "NICE",
                "source_type": "guideline",
                "source_url": "https://www.nice.org.uk/guidance/ng97/chapter/Recommendations",
                "retrieved_at": now,
                "evidence_level": "guideline",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.intervention,
            "title": "WHO建议开展身体活动以降低认知下降风险",
            "content": (
                "WHO风险降低指南提出：应推荐身体活动等生活方式干预，"
                "以延缓或预防认知下降与痴呆风险。"
            ),
            "tags": "who,physical_activity,prevention,intervention",
            "metadata_json": {
                "code": "I-WHO-PA-001",
                "source_org": "WHO",
                "source_type": "guideline",
                "source_url": "https://www.who.int/publications/i/item/risk-reduction-of-cognitive-decline-and-dementia",
                "source_date": "2019-01-01",
                "retrieved_at": now,
                "evidence_level": "guideline",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.intervention,
            "title": "认知风险干预应聚焦可改变危险因素（WHO）",
            "content": (
                "在缺乏治愈性治疗背景下，风险管理应优先聚焦可改变危险因素，"
                "将认知风险控制纳入长期慢病管理。"
            ),
            "tags": "who,risk_factor,intervention,management",
            "metadata_json": {
                "code": "I-WHO-RISKFACTOR-001",
                "source_org": "WHO",
                "source_type": "guideline",
                "source_url": "https://www.who.int/publications/i/item/risk-reduction-of-cognitive-decline-and-dementia",
                "retrieved_at": now,
                "evidence_level": "guideline",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.template,
            "title": "家属沟通模板：筛查异常需复评而非确诊",
            "content": (
                "本次结果提示存在认知风险信号，建议尽快安排专科复评。"
                "该结果用于早期筛查与分流，不能替代临床确诊。"
            ),
            "tags": "family,communication,template,safety",
            "metadata_json": {
                "template_id": "T-FAMILY-SCREENING-001",
                "source_org": "USPSTF+NICE+MoCA",
                "source_type": "derived_template",
                "source_url": "https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/cognitive-impairment-in-older-adults-screening",
                "retrieved_at": now,
                "evidence_level": "safety_template",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.template,
            "title": "医生沟通模板：先排除可逆因素再定亚型",
            "content": (
                "建议先完成可逆病因排查，再结合认知评估与必要影像/神经心理测试进行亚型判断，"
                "并据结果制定随访与干预计划。"
            ),
            "tags": "doctor,template,diagnosis,workflow",
            "metadata_json": {
                "template_id": "T-DOCTOR-DIAG-001",
                "source_org": "NICE",
                "source_type": "derived_template",
                "source_url": "https://www.nice.org.uk/guidance/ng97/chapter/Recommendations",
                "retrieved_at": now,
                "evidence_level": "guideline_template",
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
                .filter(
                    RagKnowledgeItem.title == row["title"],
                )
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
    print(f"RAG knowledge import done. created={c}, updated={u}")

