import sqlite3

conn = sqlite3.connect('cognitive.db')
cursor = conn.cursor()

# 获取assessment_results表结构
cursor.execute("PRAGMA table_info(assessment_results)")
columns = cursor.fetchall()
print('Assessment Results table columns:')
for col in columns:
    print(f'  - {col[1]} ({col[2]})')

# 查看吴爷爷的评估结果详情
cursor.execute("SELECT * FROM assessment_results WHERE id = 18")
result = cursor.fetchone()
print('\n吴爷爷的评估结果详情 (ID=18):')
col_names = [c[1] for c in columns]
for i, val in enumerate(result):
    print(f'  - {col_names[i]}: {val}')

conn.close()