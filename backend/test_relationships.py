import requests

# 先登录获取token
login_data = {'username': '13800000001', 'password': 'admin123'}
r = requests.post('http://localhost:30001/api/v1/auth/login', data=login_data)
print('登录状态:', r.status_code)
if r.status_code == 200:
    token = r.json()['access_token']
    print('获取token成功')
    
    # 获取家属关系列表
    headers = {'Authorization': f'Bearer {token}'}
    r = requests.get('http://localhost:30001/api/v1/users/family-relationships', headers=headers)
    print('家属关系列表状态:', r.status_code)
    relationships = r.json()
    print('家属关系数量:', len(relationships))
    print('\n=== 老人与家属关系列表 ===')
    for rel in relationships:
        print(f"{rel['elder_name']} ← {rel['relationship']} → {rel['family_name']}")
else:
    print('登录失败:', r.text)
