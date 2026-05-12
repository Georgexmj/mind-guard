import sqlite3

# 直接连接SQLite数据库
conn = sqlite3.connect('cognitive.db')
cursor = conn.cursor()

# 查询所有老人
cursor.execute("SELECT id, name, phone, gender, birth_date, community_id FROM users WHERE role='elder' ORDER BY id")
rows = cursor.fetchall()

print(f"数据库中的老人数量: {len(rows)}")
print("--- 详细信息 ---")
for row in rows:
    print(f"ID: {row[0]}, 姓名: {row[1]}, 电话: {row[2]}, 性别: {row[3]}, 生日: {row[4]}, 社区ID: {row[5]}")

conn.close()
