from sqlalchemy import create_engine, text
engine = create_engine('sqlite:///./cognitive.db')
with engine.connect() as conn:
    # 查询没有评估结果的会话
    result = conn.execute(text('''
        SELECT s.id, s.user_id, u.name, s.status, s.created_at, s.completed_at
        FROM assessment_sessions s
        LEFT JOIN assessment_results r ON s.id = r.session_id
        LEFT JOIN users u ON s.user_id = u.id
        WHERE s.status = "completed" AND r.id IS NULL
        ORDER BY s.created_at DESC
    '''))
    print(f"{'会话ID':<10} {'用户ID':<8} {'姓名':<8} {'状态':<10} {'创建时间':<20} {'完成时间':<20}")
    print("-" * 90)
    for row in result:
        print(f"{row[0]:<10} {row[1]:<8} {row[2]:<8} {row[3]:<10} {str(row[4]):<20} {str(row[5]):<20}")