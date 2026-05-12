from sqlalchemy import create_engine, text
engine = create_engine('sqlite:///./cognitive.db')
with engine.connect() as conn:
    # 查询所有已完成的评估会话
    result = conn.execute(text('''
        SELECT s.id, s.user_id, u.name, s.status, r.risk_level
        FROM assessment_sessions s
        LEFT JOIN assessment_results r ON s.id = r.session_id
        LEFT JOIN users u ON s.user_id = u.id
        WHERE s.status = "completed"
        ORDER BY s.created_at DESC
        LIMIT 20
    '''))
    print(f"{'会话ID':<10} {'用户ID':<8} {'姓名':<8} {'状态':<10} {'风险等级'}")
    print("-" * 60)
    for row in result:
        risk_level = row[4] if row[4] else '未生成'
        print(f"{row[0]:<10} {row[1]:<8} {row[2]:<8} {row[3]:<10} {risk_level}")