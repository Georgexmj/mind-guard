import sqlite3
from datetime import date, timedelta

conn = sqlite3.connect('cognitive.db')
cursor = conn.cursor()

# 为赵奶奶（ID=3）创建干预计划
elder_id = 3

# 检查是否已有故事复述相关的计划
cursor.execute("SELECT id, title FROM intervention_plans WHERE elder_id = ? AND title LIKE '%故事复述%'", (elder_id,))
existing_plan = cursor.fetchone()

if existing_plan:
    print(f'已存在故事复述相关计划: ID={existing_plan[0]}, 标题={existing_plan[1]}')
else:
    # 创建新的干预计划
    today = date.today()
    end_date = today + timedelta(days=30)
    
    cursor.execute('''
        INSERT INTO intervention_plans (elder_id, created_by, title, description, domain_focus, frequency, duration_days, start_date, end_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        elder_id,
        1,  # admin用户
        '故事复述训练',
        '通过故事复述练习提高语言表达和记忆能力',
        'language,memory',
        '每天一次',
        30,
        today.isoformat(),
        end_date.isoformat(),
        'active'
    ))
    
    plan_id = cursor.lastrowid
    conn.commit()
    print(f'创建干预计划成功: ID={plan_id}, 标题=故事复述训练')

conn.close()