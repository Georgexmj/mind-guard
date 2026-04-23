"""
Import China expert-consensus clinical pathway knowledge into rag_knowledge_items.

Usage:
  python -m backend.scripts.import_rag_cn_clinical_pathways
or
  cd backend && python scripts/import_rag_cn_clinical_pathways.py
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
            "title": "老年认知障碍评估流程应为“病史-体检-筛查-全面评估-ADL/BPSD-诊断-随访”闭环",
            "content": (
                "中华医学会老年医学分会共识指出，完整流程应包括一般信息、病史、体格检查、"
                "快速筛查、全面评估、ADL/BPSD评估，并结合辅助检查做出临床诊断与后续干预随访计划。"
            ),
            "tags": "中国,中华医学会老年医学分会,评估流程,ADL,BPSD,rule",
            "metadata_json": {
                "rule_id": "CN-R-GERIATRICS-2022-PATHWAY-001",
                "source_org": "中华医学会老年医学分会",
                "source_type": "expert_consensus",
                "source_title": "老年人认知障碍评估中国专家共识(2022)",
                "source_url": "https://medtion-image.medtion.com/uploads/1/file/public/202402/20240202112433_dk5lmmp311.pdf",
                "source_date": "2022-12-01",
                "doi": "10.3760/cma.j.issn.0254-9026.2022.12.006",
                "retrieved_at": now,
                "evidence_level": "expert_consensus",
                "locale": "zh-CN",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.rule,
            "title": "临床诊断不能仅凭单一量表得分，需联合病史体检与辅助检查",
            "content": (
                "老年认知障碍评估共识强调：认知量表是核心，但临床诊断不能仅依赖量表分数，"
                "应综合病史、体格检查和辅助检查后判断是否存在认知障碍、严重度和病因。"
            ),
            "tags": "中国,中华医学会老年医学分会,综合诊断,鉴别诊断,rule",
            "metadata_json": {
                "rule_id": "CN-R-GERIATRICS-2022-DIAG-001",
                "source_org": "中华医学会老年医学分会",
                "source_type": "expert_consensus",
                "source_title": "老年人认知障碍评估中国专家共识(2022)",
                "source_url": "https://medtion-image.medtion.com/uploads/1/file/public/202402/20240202112433_dk5lmmp311.pdf",
                "source_date": "2022-12-01",
                "doi": "10.3760/cma.j.issn.0254-9026.2022.12.006",
                "retrieved_at": now,
                "evidence_level": "expert_consensus",
                "locale": "zh-CN",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.rule,
            "title": "门住诊筛查与全面评估可采用“筛查量表+自评量表+他评量表”组合",
            "content": (
                "共识建议门诊或住院老年患者可先用筛查量表，再结合全面评估自评与他评量表，"
                "以提升评估覆盖度与一致性，支持后续诊断分层。"
            ),
            "tags": "中国,量表组合,筛查量表,自评,他评,rule",
            "metadata_json": {
                "rule_id": "CN-R-GERIATRICS-2022-SCALESET-001",
                "source_org": "中华医学会老年医学分会",
                "source_type": "expert_consensus",
                "source_title": "老年人认知障碍评估中国专家共识(2022)",
                "source_url": "https://medtion-image.medtion.com/uploads/1/file/public/202402/20240202112433_dk5lmmp311.pdf",
                "source_date": "2022-12-01",
                "doi": "10.3760/cma.j.issn.0254-9026.2022.12.006",
                "retrieved_at": now,
                "evidence_level": "expert_consensus",
                "locale": "zh-CN",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.rule,
            "title": "前驱期AD简筛：社区自评或基层他评异常者应转专科门诊",
            "content": (
                "中华医学会神经病学分会痴呆与认知障碍学组共识提出，"
                "简筛阶段可由社区老人自评或基层医生他评，怀疑认知障碍者应转认知/记忆/神经心理专科门诊进一步检查。"
            ),
            "tags": "中国,中华医学会神经病学分会,前驱期AD,转诊,rule",
            "metadata_json": {
                "rule_id": "CN-R-NEUROLOGY-2023-REFERRAL-001",
                "source_org": "中华医学会神经病学分会痴呆与认知障碍学组+中国医师协会神经内科医师分会",
                "source_type": "expert_consensus",
                "source_title": "前驱期阿尔茨海默病的简易筛查中国专家共识(2023年版)",
                "source_url": "https://medtion-image.medtion.com/uploads/1/file/public/202308/20230811162808_ptbf50vkki.pdf",
                "source_date": "2023-05-01",
                "doi": "10.3760/cma.j.cn115354-20230330-00191",
                "retrieved_at": now,
                "evidence_level": "expert_consensus",
                "locale": "zh-CN",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.rule,
            "title": "前驱期AD三步路径：初筛分流-中间态复筛-模棱两可者PET/CSF确证",
            "content": (
                "2023共识给出三步流程：第1步常规筛查与基础检查分层；第2步对中间状态做“亲Aβ认知测试+血标志物+MRI萎缩”再分层；"
                "第3步对仍不能确诊者进行分子PET或CSF检测明确诊断。"
            ),
            "tags": "中国,三步路径,pAD,PET,CSF,rule",
            "metadata_json": {
                "rule_id": "CN-R-NEUROLOGY-2023-3STEP-001",
                "source_org": "中华医学会神经病学分会痴呆与认知障碍学组+中国医师协会神经内科医师分会",
                "source_type": "expert_consensus",
                "source_title": "前驱期阿尔茨海默病的简易筛查中国专家共识(2023年版)",
                "source_url": "https://medtion-image.medtion.com/uploads/1/file/public/202308/20230811162808_ptbf50vkki.pdf",
                "source_date": "2023-05-01",
                "doi": "10.3760/cma.j.cn115354-20230330-00191",
                "retrieved_at": now,
                "evidence_level": "expert_consensus",
                "locale": "zh-CN",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.rule,
            "title": "前驱期AD量表组合：MMSE偏痴呆识别，MoCA/MoCA-B/ACE-III偏MCI识别",
            "content": (
                "共识指出传统神经心理测验仍是核心依据：MMSE用于辅助识别痴呆；"
                "MoCA或MoCA-B、ACE-III用于识别MCI，并可联合多认知域测验提高早期识别能力。"
            ),
            "tags": "中国,MMSE,MoCA,ACE-III,MCI,rule",
            "metadata_json": {
                "rule_id": "CN-R-NEUROLOGY-2023-SCALECOMBO-001",
                "source_org": "中华医学会神经病学分会痴呆与认知障碍学组+中国医师协会神经内科医师分会",
                "source_type": "expert_consensus",
                "source_title": "前驱期阿尔茨海默病的简易筛查中国专家共识(2023年版)",
                "source_url": "https://medtion-image.medtion.com/uploads/1/file/public/202308/20230811162808_ptbf50vkki.pdf",
                "source_date": "2023-05-01",
                "doi": "10.3760/cma.j.cn115354-20230330-00191",
                "retrieved_at": now,
                "evidence_level": "expert_consensus",
                "locale": "zh-CN",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.rule,
            "title": "淀粉样蛋白PET结果应采用全局二元判读，并与临床特征联合解释",
            "content": (
                "中华医学会神经病学分会痴呆与认知障碍学组与核医学分会共识提出，"
                "淀粉样蛋白PET建议全局二元判读（阳性/阴性），且无论结果均需结合神经心理、形态/功能影像与其他生物标志物。"
            ),
            "tags": "中国,淀粉样蛋白PET,阳性阴性,联合解释,rule",
            "metadata_json": {
                "rule_id": "CN-R-NEURO-NUCLEAR-2023-READOUT-001",
                "source_org": "中华医学会神经病学分会痴呆与认知障碍学组+中华医学会核医学分会",
                "source_type": "expert_consensus",
                "source_title": "淀粉样蛋白PET显像在阿尔茨海默病诊断中的应用专家共识",
                "source_url": "https://medtion-image.medtion.com/uploads/1/file/public/202312/20231207184036_8qwpvko69l.pdf",
                "source_date": "2023-12-05",
                "doi": "10.3760/cma.j.cn112137-20230909-00433",
                "retrieved_at": now,
                "evidence_level": "expert_consensus",
                "locale": "zh-CN",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.rule,
            "title": "早期AD有条件单位可实施淀粉样蛋白PET以提高诊断准确性",
            "content": (
                "PET共识推荐关注早期AD并在有条件单位开展淀粉样蛋白PET，"
                "用于诊断、鉴别诊断及疗效监测，为精准诊疗和转归判断提供依据。"
            ),
            "tags": "中国,早期AD,生物标志物,PET,rule",
            "metadata_json": {
                "rule_id": "CN-R-NEURO-NUCLEAR-2023-INDICATION-001",
                "source_org": "中华医学会神经病学分会痴呆与认知障碍学组+中华医学会核医学分会",
                "source_type": "expert_consensus",
                "source_title": "淀粉样蛋白PET显像在阿尔茨海默病诊断中的应用专家共识",
                "source_url": "https://medtion-image.medtion.com/uploads/1/file/public/202312/20231207184036_8qwpvko69l.pdf",
                "source_date": "2023-12-05",
                "doi": "10.3760/cma.j.cn112137-20230909-00433",
                "retrieved_at": now,
                "evidence_level": "expert_consensus",
                "locale": "zh-CN",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.rule,
            "title": "疾病修饰治疗相关路径：早期AD人群建议MMSE≥20且CDR-GS 0.5~1分",
            "content": (
                "2025专家共识建议在疾病修饰治疗相关研究路径中聚焦早期AD人群，"
                "临床分期常用阈值为MMSE≥20（小学及以上）且CDR-GS 0.5~1分。"
            ),
            "tags": "中国,中华医学会神经病学分会,早期AD,MMSE,CDR,阈值,rule",
            "metadata_json": {
                "rule_id": "CN-R-NEUROLOGY-2025-DMT-STAGE-001",
                "source_org": "中华医学会神经病学分会痴呆与认知障碍学组",
                "source_type": "expert_consensus",
                "source_title": "阿尔茨海默病疾病修饰治疗药物临床试验专家共识（2025版）",
                "source_url": "https://medtion-image.medtion.com/uploads/1/file/public/202505/20250509111844_o76bkwwuk8.pdf",
                "source_date": "2025-04-01",
                "doi": "10.3760/cma.j.cn115354-20250121-00042",
                "retrieved_at": now,
                "evidence_level": "expert_consensus",
                "locale": "zh-CN",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.rule,
            "title": "抗Aβ相关风险分层：MRI提示Fazekas≥3或CMB>4或cSS>1应视为ARIA高风险",
            "content": (
                "2025共识提出针对抗Aβ路径需做MRI风险筛选，若Fazekas评分≥3、脑微出血CMB>4或皮质表面铁沉积cSS>1，"
                "应按ARIA高风险处理并从相应路径中排除。"
            ),
            "tags": "中国,ARIA,Fazekas,CMB,cSS,风险分层,rule",
            "metadata_json": {
                "rule_id": "CN-R-NEUROLOGY-2025-ARIA-001",
                "source_org": "中华医学会神经病学分会痴呆与认知障碍学组",
                "source_type": "expert_consensus",
                "source_title": "阿尔茨海默病疾病修饰治疗药物临床试验专家共识（2025版）",
                "source_url": "https://medtion-image.medtion.com/uploads/1/file/public/202505/20250509111844_o76bkwwuk8.pdf",
                "source_date": "2025-04-01",
                "doi": "10.3760/cma.j.cn115354-20250121-00042",
                "retrieved_at": now,
                "evidence_level": "expert_consensus",
                "locale": "zh-CN",
            },
            "is_active": True,
        },
        {
            "kb_type": KnowledgeType.template,
            "title": "专科转诊模板：基层简筛异常后的认知门诊检查建议",
            "content": (
                "建议转诊至认知/记忆门诊，完善病史、体检、实验室检查、头颅CT或MRI；"
                "对介于正常衰老与痴呆之间者进一步进行亲Aβ认知测试、血标志物及MRI萎缩评估，必要时PET/CSF确证。"
            ),
            "tags": "中国,转诊模板,基层到专科,pAD,template",
            "metadata_json": {
                "template_id": "CN-T-NEUROLOGY-2023-REFERRAL-001",
                "source_org": "中华医学会神经病学分会痴呆与认知障碍学组+中国医师协会神经内科医师分会",
                "source_type": "derived_template",
                "source_title": "前驱期阿尔茨海默病的简易筛查中国专家共识(2023年版)",
                "source_url": "https://medtion-image.medtion.com/uploads/1/file/public/202308/20230811162808_ptbf50vkki.pdf",
                "source_date": "2023-05-01",
                "doi": "10.3760/cma.j.cn115354-20230330-00191",
                "retrieved_at": now,
                "evidence_level": "clinical_pathway_template",
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
    print(f"CN clinical pathway import done. created={c}, updated={u}")

