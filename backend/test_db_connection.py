import requests

# 先登录获取token
login_data = {'username': '13800000001', 'password': 'admin123'}
r = requests.post('http://localhost:8000/api/v1/auth/login', data=login_data)
print('登录状态:', r.status_code)
if r.status_code == 200:
    token = r.json()['access_token']
    print('获取token成功')
    
    # 使用token访问一个简单的端点，检查服务器信息
    headers = {'Authorization': f'Bearer {token}'}
    
    # 尝试访问用户自己的信息
    r = requests.get('http://localhost:8000/api/v1/users/me', headers=headers)
    print('用户信息状态:', r.status_code)
    if r.status_code == 200:
        user_info = r.json()
        print('用户信息:', user_info)
        
    # 检查是否有其他端点可以查看服务器状态
    r = requests.get('http://localhost:8000/health', headers=headers)
    print('健康检查:', r.status_code, r.text)
else:
    print('登录失败:', r.text)