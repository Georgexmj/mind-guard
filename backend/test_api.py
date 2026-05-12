import requests

# 测试用户 ID 为 6 的用户（从之前的日志看到的）
response = requests.post(
    'http://localhost:30001/api/v1/auth/login',
    data={'username': '13800000006', 'password': 'elder123'}
)
print('User 6 Login response:', response.status_code, response.json())

if response.status_code == 200:
    token = response.json().get('access_token')
    print('Token:', token[:20] if token else None, '...')
    
    # 测试创建会话
    response = requests.post(
        'http://localhost:30001/api/v1/assessments/sessions',
        headers={'Authorization': f'Bearer {token}'}
    )
    print('Create session response:', response.status_code, response.json())
