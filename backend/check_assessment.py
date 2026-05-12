import sqlite3

conn = sqlite3.connect('cognitive.db')
cursor = conn.cursor()

# 查找吴爷爷
cursor.execute("SELECT id, name, phone FROM users WHERE phone = '13800000011'")
user = cursor.fetchone()
print('吴爷爷:', user)
elder_id = user[0] if user else None

if elder_id:
    # 查找评估会话
    cursor.execute("SELECT id, status, completed_at FROM assessment_sessions WHERE user_id = ? ORDER BY created_at DESC", (elder_id,))
    sessions = cursor.fetchall()
    print(f'\n评估会话 ({len(sessions)}):')
    for session in sessions:
        session_id = session[0]
        print(f'  - ID: {session_id}, 状态: {session[1]}, 完成时间: {session[2]}')
        
        # 查找评估结果
        cursor.execute("SELECT id, risk_level, mmse_score, created_at FROM assessment_results WHERE session_id = ?", (session_id,))
        result = cursor.fetchone()
        if result:
            print(f'    评估结果: ID={result[0]}, 风险等级={result[1]}, MMSE={result[2]}')
        else:
            print(f'    评估结果: 未找到')

conn.close()