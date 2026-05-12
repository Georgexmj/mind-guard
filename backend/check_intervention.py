import sqlite3

conn = sqlite3.connect('cognitive.db')
cursor = conn.cursor()

# 查找赵奶奶
cursor.execute('SELECT id, name, phone FROM users WHERE id = 3')
print('赵奶奶:', cursor.fetchone())

# 查找她的干预计划
cursor.execute("SELECT id, title, elder_id FROM intervention_plans WHERE elder_id = 3 AND status = 'active'")
plans = cursor.fetchall()
print('\n赵奶奶的活跃干预计划:')
for plan in plans:
    print(f'  - ID: {plan[0]}, 标题: {plan[1]}')
    
    # 检查今天的记录
    cursor.execute("SELECT id, completed, created_at FROM intervention_records WHERE plan_id = ? AND record_date = date('now')", (plan[0],))
    records = cursor.fetchall()
    print(f'    今日记录: {len(records)}')
    for r in records:
        print(f'      - completed: {r[1]}, created_at: {r[2]}')

# 检查训练报告
cursor.execute("SELECT id, course_name, completed_at FROM training_reports WHERE elder_id = 3 ORDER BY completed_at DESC LIMIT 5")
reports = cursor.fetchall()
print('\n最近的训练报告:')
for report in reports:
    print(f'  - {report[1]} at {report[2]}')

conn.close()