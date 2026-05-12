from sqlalchemy import create_engine, text
engine = create_engine('sqlite:///./cognitive.db')
with engine.connect() as conn:
    result = conn.execute(text('SELECT id, name, phone, role FROM users ORDER BY id'))
    print(f"{'ID':<5} {'姓名':<10} {'电话':<15} {'角色'}")
    print("-" * 40)
    for row in result:
        print(f"{row[0]:<5} {row[1]:<10} {row[2]:<15} {row[3]}")
    
    # 统计各角色数量
    result2 = conn.execute(text('SELECT role, COUNT(*) as count FROM users GROUP BY role'))
    print("\n角色统计:")
    for row in result2:
        print(f"  {row[0]}: {row[1]}人")