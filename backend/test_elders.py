import requests
import json

# 先登录获取token
login_data = {'username': '13800000001', 'password': 'admin123'}
r = requests.post('http://localhost:8000/api/v1/auth/login', data=login_data)
print('登录状态:', r.status_code)
if r.status_code == 200:
    token = r.json()['access_token']
    print('获取token成功')
    
    # 使用token访问老人列表
    headers = {'Authorization': f'Bearer {token}'}
    r = requests.get('http://localhost:8000/api/v1/users/elders', headers=headers)
    print('老人列表状态:', r.status_code)
    elders = r.json()
    print('老人数量:', len(elders))
    print('--- 完整JSON响应 ---')
    print(json.dumps(elders, indent=2, ensure_ascii=False))
else:
    print('登录失败:', r.text)
