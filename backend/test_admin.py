import sqlite3

conn = sqlite3.connect('cognitive.db')
cursor = conn.cursor()

# 获取users表结构
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
print('Users table columns:')
for col in columns:
    print(f'  - {col[1]} ({col[2]})')

# 查找admin用户
cursor.execute("SELECT id, name, phone, role FROM users WHERE role = 'admin'")
admins = cursor.fetchall()
print('\nAdmin users:')
for admin in admins:
    print(f'  - ID: {admin[0]}, Name: {admin[1]}, Phone: {admin[2]}')

conn.close()