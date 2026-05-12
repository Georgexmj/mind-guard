"""
Seed script for base entities and question bank.

Usage:
    python -m app.initial_data
"""

import os
import sys
from datetime import date
from typing import Dict, Tuple

# Ensure backend directory is on PYTHONPATH when run as a script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models.assessment import Question, QuestionDomain, QuestionType
from app.models.user import Community, User, UserRelationship, UserRole
from app.question_bank_data import QUESTION_BANK
from app.question_bank_extra_data import EXTRA_QUESTION_BANK

import app.models.assessment  # noqa: F401 (register models)
import app.models.intervention  # noqa: F401 (register models)
import app.models.notification  # noqa: F401 (register models)
import app.models.user  # noqa: F401 (register models)
import app.models.rag  # noqa: F401 (register models)
from app.models.rag import KnowledgeType, RagKnowledgeItem


def _normalize_text(value: str) -> str:
    return " ".join((value or "").strip().split())


def _question_signature(domain: QuestionDomain, q_type: QuestionType, content: str) -> str:
    return f"{domain.value}|{q_type.value}|{_normalize_text(content).lower()}"


def seed_community(db) -> Community:
    community = db.query(Community).filter(Community.name == "幸福社区").first()
    if community is None:
        community = Community(
            name="幸福社区",
            province="湖南省",
            city="张家界市",
            district="永定区",
            address="张家界市永定区解放路街道幸福社区",
            elder_count=0,
        )
        db.add(community)
        db.flush()
        print(f"  Created community: {community.name} (id={community.id})")
    else:
        print(f"  Community already exists: {community.name}")
    return community


def seed_users(db, community_id: int) -> None:
    users_to_seed = [
        {
            "phone": "13800000001",
            "name": "系统管理员",
            "gender": "male",
            "birth_date": date(1980, 1, 1),
            "education_years": 16,
            "role": UserRole.admin,
            "password": "admin123",
        },
        {
            "phone": "13800000002",
            "name": "张医生",
            "gender": "female",
            "birth_date": date(1985, 5, 20),
            "education_years": 20,
            "role": UserRole.doctor,
            "password": "doctor123",
        },
        # 原有老人
        {
            "phone": "13800000003",
            "id_card": "123456194808151234",
            "name": "李奶奶",
            "gender": "female",
            "birth_date": date(1948, 8, 15),
            "education_years": 6,
            "role": UserRole.elder,
            "password": "elder123",
        },
        {
            "phone": "13800000005",
            "id_card": "430802194511234567",
            "name": "王爷爷",
            "gender": "male",
            "birth_date": date(1945, 11, 23),
            "education_years": 9,
            "role": UserRole.elder,
            "password": "elder123",
        },
        {
            "phone": "13800000006",
            "id_card": "430802195003156789",
            "name": "赵奶奶",
            "gender": "female",
            "birth_date": date(1950, 3, 15),
            "education_years": 12,
            "role": UserRole.elder,
            "password": "elder123",
        },
        {
            "phone": "13800000007",
            "id_card": "430802194706123456",
            "name": "刘爷爷",
            "gender": "male",
            "birth_date": date(1947, 6, 12),
            "education_years": 6,
            "role": UserRole.elder,
            "password": "elder123",
        },
        {
            "phone": "13800000008",
            "id_card": "430802194909287890",
            "name": "陈奶奶",
            "gender": "female",
            "birth_date": date(1949, 9, 28),
            "education_years": 3,
            "role": UserRole.elder,
            "password": "elder123",
        },
        {
            "phone": "13800000009",
            "id_card": "430802194604051234",
            "name": "孙爷爷",
            "gender": "male",
            "birth_date": date(1946, 4, 5),
            "education_years": 12,
            "role": UserRole.elder,
            "password": "elder123",
        },
        {
            "phone": "13800000010",
            "id_card": "430802195207185678",
            "name": "周奶奶",
            "gender": "female",
            "birth_date": date(1952, 7, 18),
            "education_years": 9,
            "role": UserRole.elder,
            "password": "elder123",
        },
        {
            "phone": "13800000011",
            "id_card": "430802194412089012",
            "name": "吴爷爷",
            "gender": "male",
            "birth_date": date(1944, 12, 8),
            "education_years": 6,
            "role": UserRole.elder,
            "password": "elder123",
        },
        {
            "phone": "13800000012",
            "id_card": "430802195101203456",
            "name": "郑奶奶",
            "gender": "female",
            "birth_date": date(1951, 1, 20),
            "education_years": 12,
            "role": UserRole.elder,
            "password": "elder123",
        },
        {
            "phone": "13800000013",
            "id_card": "430802194305156789",
            "name": "黄爷爷",
            "gender": "male",
            "birth_date": date(1943, 5, 15),
            "education_years": 3,
            "role": UserRole.elder,
            "password": "elder123",
        },
        {
            "phone": "13800000014",
            "id_card": "430802195310089012",
            "name": "冯奶奶",
            "gender": "female",
            "birth_date": date(1953, 10, 8),
            "education_years": 6,
            "role": UserRole.elder,
            "password": "elder123",
        },
        # 新增老人
        {
            "phone": "13800000016",
            "id_card": "430802194202281234",
            "name": "许爷爷",
            "gender": "male",
            "birth_date": date(1942, 2, 28),
            "education_years": 9,
            "role": UserRole.elder,
            "password": "elder123",
        },
        {
            "phone": "13800000017",
            "id_card": "430802195411125678",
            "name": "杨奶奶",
            "gender": "female",
            "birth_date": date(1954, 11, 12),
            "education_years": 6,
            "role": UserRole.elder,
            "password": "elder123",
        },
        {
            "phone": "13800000018",
            "id_card": "430802194107089012",
            "name": "何爷爷",
            "gender": "male",
            "birth_date": date(1941, 7, 8),
            "education_years": 12,
            "role": UserRole.elder,
            "password": "elder123",
        },
        {
            "phone": "13800000019",
            "id_card": "430802195504153456",
            "name": "梁奶奶",
            "gender": "female",
            "birth_date": date(1955, 4, 15),
            "education_years": 3,
            "role": UserRole.elder,
            "password": "elder123",
        },
        {
            "phone": "13800000020",
            "id_card": "430802194009207890",
            "name": "谢爷爷",
            "gender": "male",
            "birth_date": date(1940, 9, 20),
            "education_years": 6,
            "role": UserRole.elder,
            "password": "elder123",
        },
        {
            "phone": "13800000021",
            "id_card": "430802195601251234",
            "name": "苏奶奶",
            "gender": "female",
            "birth_date": date(1956, 1, 25),
            "education_years": 9,
            "role": UserRole.elder,
            "password": "elder123",
        },
        {
            "phone": "13800000022",
            "id_card": "430802193906105678",
            "name": "马爷爷",
            "gender": "male",
            "birth_date": date(1939, 6, 10),
            "education_years": 12,
            "role": UserRole.elder,
            "password": "elder123",
        },
        {
            "phone": "13800000023",
            "id_card": "430802195708089012",
            "name": "罗奶奶",
            "gender": "female",
            "birth_date": date(1957, 8, 8),
            "education_years": 6,
            "role": UserRole.elder,
            "password": "elder123",
        },
        {
            "phone": "13800000024",
            "id_card": "430802193812203456",
            "name": "郭爷爷",
            "gender": "male",
            "birth_date": date(1938, 12, 20),
            "education_years": 3,
            "role": UserRole.elder,
            "password": "elder123",
        },
        {
            "phone": "13800000025",
            "id_card": "430802195803187890",
            "name": "林奶奶",
            "gender": "female",
            "birth_date": date(1958, 3, 18),
            "education_years": 9,
            "role": UserRole.elder,
            "password": "elder123",
        },
        # 家属用户
        {
            "phone": "13800000004",
            "name": "李女士",
            "gender": "female",
            "birth_date": date(1978, 3, 9),
            "education_years": 12,
            "role": UserRole.family,
            "password": "family123",
        },
        {
            "phone": "13800000015",
            "name": "王先生",
            "gender": "male",
            "birth_date": date(1975, 8, 12),
            "education_years": 16,
            "role": UserRole.family,
            "password": "family123",
        },
        {
            "phone": "13800000026",
            "name": "王女士",
            "gender": "female",
            "birth_date": date(1976, 4, 15),
            "education_years": 14,
            "role": UserRole.family,
            "password": "family123",
        },
        {
            "phone": "13800000027",
            "name": "赵先生",
            "gender": "male",
            "birth_date": date(1972, 11, 3),
            "education_years": 16,
            "role": UserRole.family,
            "password": "family123",
        },
        {
            "phone": "13800000028",
            "name": "刘女士",
            "gender": "female",
            "birth_date": date(1980, 6, 20),
            "education_years": 12,
            "role": UserRole.family,
            "password": "family123",
        },
        {
            "phone": "13800000029",
            "name": "陈先生",
            "gender": "male",
            "birth_date": date(1974, 9, 12),
            "education_years": 18,
            "role": UserRole.family,
            "password": "family123",
        },
        {
            "phone": "13800000030",
            "name": "孙女士",
            "gender": "female",
            "birth_date": date(1977, 2, 28),
            "education_years": 14,
            "role": UserRole.family,
            "password": "family123",
        },
        {
            "phone": "13800000031",
            "name": "周先生",
            "gender": "male",
            "birth_date": date(1973, 7, 8),
            "education_years": 16,
            "role": UserRole.family,
            "password": "family123",
        },
        {
            "phone": "13800000032",
            "name": "吴女士",
            "gender": "female",
            "birth_date": date(1979, 12, 15),
            "education_years": 12,
            "role": UserRole.family,
            "password": "family123",
        },
        {
            "phone": "13800000033",
            "name": "郑先生",
            "gender": "male",
            "birth_date": date(1971, 1, 20),
            "education_years": 18,
            "role": UserRole.family,
            "password": "family123",
        },
        {
            "phone": "13800000034",
            "name": "黄女士",
            "gender": "female",
            "birth_date": date(1978, 5, 25),
            "education_years": 14,
            "role": UserRole.family,
            "password": "family123",
        },
        {
            "phone": "13800000035",
            "name": "冯先生",
            "gender": "male",
            "birth_date": date(1976, 10, 3),
            "education_years": 16,
            "role": UserRole.family,
            "password": "family123",
        },
        {
            "phone": "13800000036",
            "name": "许女士",
            "gender": "female",
            "birth_date": date(1982, 2, 10),
            "education_years": 12,
            "role": UserRole.family,
            "password": "family123",
        },
        {
            "phone": "13800000037",
            "name": "杨先生",
            "gender": "male",
            "birth_date": date(1974, 11, 28),
            "education_years": 16,
            "role": UserRole.family,
            "password": "family123",
        },
        {
            "phone": "13800000038",
            "name": "何女士",
            "gender": "female",
            "birth_date": date(1975, 7, 15),
            "education_years": 14,
            "role": UserRole.family,
            "password": "family123",
        },
        {
            "phone": "13800000039",
            "name": "梁先生",
            "gender": "male",
            "birth_date": date(1979, 4, 8),
            "education_years": 18,
            "role": UserRole.family,
            "password": "family123",
        },
        {
            "phone": "13800000040",
            "name": "谢女士",
            "gender": "female",
            "birth_date": date(1981, 9, 30),
            "education_years": 12,
            "role": UserRole.family,
            "password": "family123",
        },
        {
            "phone": "13800000041",
            "name": "苏先生",
            "gender": "male",
            "birth_date": date(1977, 1, 10),
            "education_years": 16,
            "role": UserRole.family,
            "password": "family123",
        },
        {
            "phone": "13800000042",
            "name": "马女士",
            "gender": "female",
            "birth_date": date(1973, 6, 18),
            "education_years": 14,
            "role": UserRole.family,
            "password": "family123",
        },
        {
            "phone": "13800000043",
            "name": "罗先生",
            "gender": "male",
            "birth_date": date(1978, 8, 22),
            "education_years": 12,
            "role": UserRole.family,
            "password": "family123",
        },
        {
            "phone": "13800000044",
            "name": "郭女士",
            "gender": "female",
            "birth_date": date(1980, 12, 5),
            "education_years": 16,
            "role": UserRole.family,
            "password": "family123",
        },
        {
            "phone": "13800000045",
            "name": "林先生",
            "gender": "male",
            "birth_date": date(1976, 3, 28),
            "education_years": 14,
            "role": UserRole.family,
            "password": "family123",
        },
    ]

    for item in users_to_seed:
        user = db.query(User).filter(User.phone == item["phone"]).first()
        if user is None:
            user = User(
                phone=item["phone"],
                id_card=item.get("id_card"),
                name=item["name"],
                gender=item["gender"],
                birth_date=item["birth_date"],
                education_years=item["education_years"],
                role=item["role"],
                community_id=community_id,
                password_hash=hash_password(item["password"]),
                is_active=True,
            )
            db.add(user)
            print(f"  Created {item['role'].value} user: {item['phone']} / {item['password']}")
        else:
            print(f"  User already exists: {item['phone']} ({item['role'].value})")

    # SessionLocal uses autoflush=False; flush pending inserts before relationship queries.
    db.flush()

    # 定义老人与家属的关系映射
    relationships = [
        ("13800000003", "13800000004", "daughter"),   # 李奶奶 - 李女士(女儿)
        ("13800000005", "13800000015", "son"),        # 王爷爷 - 王先生(儿子)
        ("13800000006", "13800000027", "son"),        # 赵奶奶 - 赵先生(儿子)
        ("13800000007", "13800000028", "daughter"),   # 刘爷爷 - 刘女士(女儿)
        ("13800000008", "13800000029", "son"),        # 陈奶奶 - 陈先生(儿子)
        ("13800000009", "13800000030", "daughter"),   # 孙爷爷 - 孙女士(女儿)
        ("13800000010", "13800000031", "son"),        # 周奶奶 - 周先生(儿子)
        ("13800000011", "13800000032", "daughter"),   # 吴爷爷 - 吴女士(女儿)
        ("13800000012", "13800000033", "son"),        # 郑奶奶 - 郑先生(儿子)
        ("13800000013", "13800000034", "daughter"),   # 黄爷爷 - 黄女士(女儿)
        ("13800000014", "13800000035", "son"),        # 冯奶奶 - 冯先生(儿子)
        ("13800000016", "13800000036", "daughter"),   # 许爷爷 - 许女士(女儿)
        ("13800000017", "13800000037", "son"),        # 杨奶奶 - 杨先生(儿子)
        ("13800000018", "13800000038", "daughter"),   # 何爷爷 - 何女士(女儿)
        ("13800000019", "13800000039", "son"),        # 梁奶奶 - 梁先生(儿子)
        ("13800000020", "13800000040", "daughter"),   # 谢爷爷 - 谢女士(女儿)
        ("13800000021", "13800000041", "son"),        # 苏奶奶 - 苏先生(儿子)
        ("13800000022", "13800000042", "daughter"),   # 马爷爷 - 马女士(女儿)
        ("13800000023", "13800000043", "son"),        # 罗奶奶 - 罗先生(儿子)
        ("13800000024", "13800000044", "daughter"),   # 郭爷爷 - 郭女士(女儿)
        ("13800000025", "13800000045", "son"),        # 林奶奶 - 林先生(儿子)
    ]

    for elder_phone, family_phone, relationship in relationships:
        elder = db.query(User).filter(User.phone == elder_phone, User.role == UserRole.elder).first()
        family = db.query(User).filter(User.phone == family_phone, User.role == UserRole.family).first()
        if elder and family:
            existing_relation = (
                db.query(UserRelationship)
                .filter(
                    UserRelationship.elder_id == elder.id,
                    UserRelationship.family_id == family.id,
                )
                .first()
            )
            if existing_relation is None:
                db.add(
                    UserRelationship(
                        elder_id=elder.id,
                        family_id=family.id,
                        relationship=relationship,
                        notify_level=1,
                        is_primary=True,
                    )
                )
                print(f"  Created family relationship: {family_phone} -> {elder_phone} ({relationship})")


def seed_question_bank(db) -> Tuple[int, int, Dict[str, int]]:
    existing_questions = db.query(Question).all()
    existing_map = {
        _question_signature(q.domain, q.q_type, q.content): q for q in existing_questions
    }

    added = 0
    updated = 0

    for q_data in QUESTION_BANK + EXTRA_QUESTION_BANK:
        signature = _question_signature(
            q_data["domain"],
            q_data["q_type"],
            q_data["content"],
        )
        existing = existing_map.get(signature)
        if existing is None:
            db.add(
                Question(
                    domain=q_data["domain"],
                    q_type=q_data["q_type"],
                    content=q_data["content"],
                    options=q_data.get("options"),
                    correct_answer=q_data.get("correct_answer"),
                    difficulty=q_data["difficulty"],
                    irt_a=q_data["irt_a"],
                    irt_b=q_data["irt_b"],
                    is_active=bool(q_data.get("is_active", True)),
                )
            )
            added += 1
            continue

        changed = False
        for field in (
            "options",
            "correct_answer",
            "difficulty",
            "irt_a",
            "irt_b",
            "is_active",
        ):
            incoming = q_data.get(field)
            if getattr(existing, field) != incoming:
                setattr(existing, field, incoming)
                changed = True
        if changed:
            updated += 1

    # SessionLocal uses autoflush=False, so flush pending inserts before counting.
    db.flush()

    domain_counter: Dict[str, int] = {}
    for domain in QuestionDomain:
        count = (
            db.query(Question)
            .filter(Question.domain == domain, Question.is_active == True)
            .count()
        )
        domain_counter[domain.value] = count
    return added, updated, domain_counter


def seed_rag_knowledge(db) -> Tuple[int, int]:
    base_items = [
        {
            "kb_type": KnowledgeType.rule,
            "title": "MoCA 受教育年限校正规则",
            "content": "当受教育年限为0年时，MoCA总分加1分进行校正，最高不超过30分。",
            "tags": "moca,education,rule",
            "metadata_json": {"rule_id": "R-MOCA-EDU-001", "priority": "hard"},
        },
        {
            "kb_type": KnowledgeType.rule,
            "title": "高风险转诊触发条件",
            "content": "当评估结果为high_risk或出现快速下降趋势时，建议尽快转诊神经内科/记忆门诊复评。",
            "tags": "risk,referral,rule",
            "metadata_json": {"rule_id": "R-REF-001", "priority": "hard"},
        },
        {
            "kb_type": KnowledgeType.intervention,
            "title": "记忆域薄弱干预建议",
            "content": "建议每日进行15-20分钟记忆训练（词语回忆、故事复述），每周复盘完成率。",
            "tags": "memory,intervention,training",
            "metadata_json": {"code": "I-MEM-001", "frequency": "daily"},
        },
        {
            "kb_type": KnowledgeType.template,
            "title": "家属解释模板-轻度风险",
            "content": "当前结果提示存在轻度认知风险，建议1-3个月内复评，并保持规律作息与认知训练。",
            "tags": "family,template,mild_risk",
            "metadata_json": {"template_id": "T-FAM-001"},
        },
    ]

    existing = {
        (item.kb_type.value, _normalize_text(item.title).lower())
        for item in db.query(RagKnowledgeItem).all()
    }
    created = 0
    updated = 0
    for row in base_items:
        key = (row["kb_type"].value, _normalize_text(row["title"]).lower())
        if key in existing:
            # keep idempotent behavior; do not overwrite user-edited content
            continue
        db.add(RagKnowledgeItem(**row))
        created += 1

    return created, updated


def seed() -> None:
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("Seeding community...")
        community = seed_community(db)

        print("Seeding users...")
        seed_users(db, community.id)

        print("Syncing question bank...")
        added, updated, domain_counter = seed_question_bank(db)
        rag_created, _ = seed_rag_knowledge(db)

        db.commit()
        total_questions = db.query(Question).filter(Question.is_active == True).count()
        print(f"  Question sync done: added={added}, updated={updated}, active_total={total_questions}")
        print(f"  Domain distribution: {domain_counter}")
        print(f"  RAG knowledge seeded: created={rag_created}")
        print("Seed completed successfully.")
    except Exception as exc:
        db.rollback()
        print(f"Seed failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
