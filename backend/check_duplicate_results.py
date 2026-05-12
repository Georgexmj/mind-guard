import sqlite3

conn = sqlite3.connect('cognitive.db')
cursor = conn.cursor()

# 查找吴爷爷的评估会话和结果
elder_id = 11  # 吴爷爷

# 查找所有评估会话
cursor.execute("SELECT id, status, completed_at FROM assessment_sessions WHERE user_id = ? ORDER BY created_at DESC", (elder_id,))
sessions = cursor.fetchall()
print(f'吴爷爷的评估会话 ({len(sessions)}):')
for session in sessions:
    session_id = session[0]
    print(f'  - 会话ID: {session_id}, 状态: {session[1]}, 完成时间: {session[2]}')
    
    # 查找该会话的所有评估结果
    cursor.execute("SELECT id, risk_level, mmse_score, created_at FROM assessment_results WHERE session_id = ?", (session_id,))
    results = cursor.fetchall()
    print(f'    评估结果数量: {len(results)}')
    for result in results:
        print(f'      - 结果ID: {result[0]}, 风险等级: {result[1]}, MMSE: {result[2]}, 创建时间: {result[3]}')

conn.close()