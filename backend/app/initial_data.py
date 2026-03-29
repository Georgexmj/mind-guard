"""
Seed script for initial data.

Usage:
    python -m app.initial_data
    # or from project root:
    python backend/app/initial_data.py

Seeds:
    - 1 Community (张家界市永定区幸福社区)
    - 3 Users: admin, doctor, elder
    - 20 Questions covering all 6 cognitive domains
"""

import sys
import os

# Ensure the backend directory is on the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from app.database import Base, engine, SessionLocal
from app.core.security import hash_password
from app.models.user import Community, User, UserRole
from app.models.assessment import Question, QuestionDomain, QuestionType

import app.models.user  # noqa: F401 — register models
import app.models.assessment  # noqa: F401 — register models


SAMPLE_QUESTIONS = [
    # ── MEMORY (4 questions) ────────────────────────────────────────────────
    {
        "domain": QuestionDomain.memory,
        "q_type": QuestionType.choice,
        "content": "请记住以下三个词：苹果、汽车、诚实。稍后我会请您回忆它们。\n现在，请问您刚才记忆的第一个词是什么？",
        "options": ["苹果", "香蕉", "桌子", "书本"],
        "correct_answer": "苹果",
        "difficulty": 0.3,
        "irt_a": 1.2,
        "irt_b": -0.8,
    },
    {
        "domain": QuestionDomain.memory,
        "q_type": QuestionType.choice,
        "content": "几分钟前您记忆了三个词。请问第二个词是什么？",
        "options": ["汽车", "飞机", "自行车", "火车"],
        "correct_answer": "汽车",
        "difficulty": 0.5,
        "irt_a": 1.0,
        "irt_b": 0.0,
    },
    {
        "domain": QuestionDomain.memory,
        "q_type": QuestionType.voice,
        "content": "请回忆并说出之前记忆的第三个词。",
        "options": None,
        "correct_answer": "诚实",
        "difficulty": 0.6,
        "irt_a": 0.9,
        "irt_b": 0.2,
    },
    {
        "domain": QuestionDomain.memory,
        "q_type": QuestionType.choice,
        "content": "以下哪位是中国的国父（中华民国开国先驱）？",
        "options": ["毛泽东", "孙中山", "邓小平", "蒋介石"],
        "correct_answer": "孙中山",
        "difficulty": 0.4,
        "irt_a": 1.1,
        "irt_b": -0.3,
    },

    # ── ORIENTATION (4 questions) ───────────────────────────────────────────
    {
        "domain": QuestionDomain.orientation,
        "q_type": QuestionType.choice,
        "content": "现在是哪一年？",
        "options": ["2024年", "2025年", "2026年", "2023年"],
        "correct_answer": "2026年",
        "difficulty": 0.2,
        "irt_a": 1.5,
        "irt_b": -1.2,
    },
    {
        "domain": QuestionDomain.orientation,
        "q_type": QuestionType.choice,
        "content": "今天是星期几？（请选择当前正确的星期）",
        "options": ["星期一", "星期三", "星期五", "星期日"],
        "correct_answer": "星期五",
        "difficulty": 0.4,
        "irt_a": 1.0,
        "irt_b": -0.2,
    },
    {
        "domain": QuestionDomain.orientation,
        "q_type": QuestionType.voice,
        "content": "请问您现在在哪个城市？",
        "options": None,
        "correct_answer": None,
        "difficulty": 0.2,
        "irt_a": 1.3,
        "irt_b": -1.5,
    },
    {
        "domain": QuestionDomain.orientation,
        "q_type": QuestionType.choice,
        "content": "现在大约是什么季节？",
        "options": ["春季", "夏季", "秋季", "冬季"],
        "correct_answer": "春季",
        "difficulty": 0.3,
        "irt_a": 1.1,
        "irt_b": -0.7,
    },

    # ── LANGUAGE (3 questions) ──────────────────────────────────────────────
    {
        "domain": QuestionDomain.language,
        "q_type": QuestionType.voice,
        "content": "请用一句完整的话描述以下场景：一位老奶奶在公园里喂鸽子。",
        "options": None,
        "correct_answer": None,
        "difficulty": 0.5,
        "irt_a": 0.8,
        "irt_b": 0.1,
    },
    {
        "domain": QuestionDomain.language,
        "q_type": QuestionType.choice,
        "content": "请选出与"医生"职业最相关的词：",
        "options": ["病人", "厨师", "司机", "教师"],
        "correct_answer": "病人",
        "difficulty": 0.3,
        "irt_a": 1.2,
        "irt_b": -0.9,
    },
    {
        "domain": QuestionDomain.language,
        "q_type": QuestionType.voice,
        "content": "请在30秒内尽可能多地说出以字母"水"开头的词语（例如：水果、水库……）。",
        "options": None,
        "correct_answer": None,
        "difficulty": 0.7,
        "irt_a": 0.9,
        "irt_b": 0.5,
    },

    # ── ATTENTION (3 questions) ─────────────────────────────────────────────
    {
        "domain": QuestionDomain.attention,
        "q_type": QuestionType.choice,
        "content": "请从100开始，每次减7，连续减5次，第一次结果是多少？",
        "options": ["93", "97", "91", "95"],
        "correct_answer": "93",
        "difficulty": 0.5,
        "irt_a": 1.3,
        "irt_b": 0.1,
    },
    {
        "domain": QuestionDomain.attention,
        "q_type": QuestionType.choice,
        "content": "继续上题：93 - 7 = ？",
        "options": ["86", "84", "88", "80"],
        "correct_answer": "86",
        "difficulty": 0.5,
        "irt_a": 1.3,
        "irt_b": 0.1,
    },
    {
        "domain": QuestionDomain.attention,
        "q_type": QuestionType.scale,
        "content": "请评估您在过去一周内，完成日常任务时的注意力集中程度。\n0 = 完全无法集中，10 = 完全可以集中",
        "options": None,
        "correct_answer": None,
        "difficulty": 0.4,
        "irt_a": 0.7,
        "irt_b": -0.3,
    },

    # ── VISUOSPATIAL (3 questions) ──────────────────────────────────────────
    {
        "domain": QuestionDomain.visuospatial,
        "q_type": QuestionType.drawing,
        "content": "请在下方画布上画一个时钟，显示时间为11点10分。需要画出表盘、所有数字（1-12）和指针。",
        "options": None,
        "correct_answer": None,
        "difficulty": 0.7,
        "irt_a": 1.0,
        "irt_b": 0.4,
    },
    {
        "domain": QuestionDomain.visuospatial,
        "q_type": QuestionType.choice,
        "content": "如果您面朝北方，向右转90度，您现在面朝哪个方向？",
        "options": ["东方", "西方", "南方", "北方"],
        "correct_answer": "东方",
        "difficulty": 0.5,
        "irt_a": 1.1,
        "irt_b": 0.0,
    },
    {
        "domain": QuestionDomain.visuospatial,
        "q_type": QuestionType.drawing,
        "content": "请在画布上临摹下面的图形：两个相互交叉的五边形。",
        "options": None,
        "correct_answer": None,
        "difficulty": 0.6,
        "irt_a": 0.9,
        "irt_b": 0.3,
    },

    # ── EXECUTIVE (3 questions) ─────────────────────────────────────────────
    {
        "domain": QuestionDomain.executive,
        "q_type": QuestionType.voice,
        "content": "如果您在街上发现了一封已经写好地址并贴好邮票但没有投入邮箱的信，您会怎么做？请说明您的处理步骤。",
        "options": None,
        "correct_answer": None,
        "difficulty": 0.6,
        "irt_a": 0.8,
        "irt_b": 0.2,
    },
    {
        "domain": QuestionDomain.executive,
        "q_type": QuestionType.choice,
        "content": "下面哪种行为体现了良好的计划能力？",
        "options": [
            "出门前查看天气预报并带伞",
            "随时随地想到什么就做什么",
            "等问题出现后再解决",
            "依赖他人安排所有事情",
        ],
        "correct_answer": "出门前查看天气预报并带伞",
        "difficulty": 0.3,
        "irt_a": 1.4,
        "irt_b": -0.8,
    },
    {
        "domain": QuestionDomain.executive,
        "q_type": QuestionType.scale,
        "content": "请评估您在过去一个月中，独立完成复杂任务（如购物计划、出行安排）的能力。\n0 = 完全无法独立完成，10 = 完全可以独立完成",
        "options": None,
        "correct_answer": None,
        "difficulty": 0.4,
        "irt_a": 0.8,
        "irt_b": -0.2,
    },
]


def seed():
    """Run all seed operations."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # ── Community ──────────────────────────────────────────────────────
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
            db.flush()  # Get community.id before committing
            print(f"  Created community: {community.name} (id={community.id})")
        else:
            print(f"  Community already exists: {community.name}")

        # ── Admin user ─────────────────────────────────────────────────────
        admin = db.query(User).filter(User.phone == "13800000001").first()
        if admin is None:
            admin = User(
                phone="13800000001",
                name="系统管理员",
                gender="male",
                birth_date=date(1980, 1, 1),
                education_years=16,
                role=UserRole.admin,
                community_id=community.id,
                password_hash=hash_password("admin123"),
                is_active=True,
            )
            db.add(admin)
            print("  Created admin user: 13800000001 / admin123")
        else:
            print("  Admin user already exists")

        # ── Doctor user ────────────────────────────────────────────────────
        doctor = db.query(User).filter(User.phone == "13800000002").first()
        if doctor is None:
            doctor = User(
                phone="13800000002",
                name="张医生",
                gender="female",
                birth_date=date(1985, 5, 20),
                education_years=20,
                role=UserRole.doctor,
                community_id=community.id,
                password_hash=hash_password("doctor123"),
                is_active=True,
            )
            db.add(doctor)
            print("  Created doctor user: 13800000002 / doctor123")
        else:
            print("  Doctor user already exists")

        # ── Elder user ─────────────────────────────────────────────────────
        elder = db.query(User).filter(User.phone == "13800000003").first()
        if elder is None:
            elder = User(
                phone="13800000003",
                name="李奶奶",
                gender="female",
                birth_date=date(1948, 8, 15),
                education_years=6,
                role=UserRole.elder,
                community_id=community.id,
                password_hash=hash_password("elder123"),
                is_active=True,
            )
            db.add(elder)
            print("  Created elder user: 13800000003 / elder123")
        else:
            print("  Elder user already exists")

        # ── Questions ──────────────────────────────────────────────────────
        existing_q_count = db.query(Question).count()
        if existing_q_count == 0:
            for q_data in SAMPLE_QUESTIONS:
                question = Question(
                    domain=q_data["domain"],
                    q_type=q_data["q_type"],
                    content=q_data["content"],
                    options=q_data.get("options"),
                    correct_answer=q_data.get("correct_answer"),
                    difficulty=q_data["difficulty"],
                    irt_a=q_data["irt_a"],
                    irt_b=q_data["irt_b"],
                    is_active=True,
                )
                db.add(question)
            print(f"  Created {len(SAMPLE_QUESTIONS)} sample questions")
        else:
            print(f"  Questions already exist ({existing_q_count} found), skipping")

        db.commit()
        print("\nSeed completed successfully.")

    except Exception as exc:
        db.rollback()
        print(f"\nSeed failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
