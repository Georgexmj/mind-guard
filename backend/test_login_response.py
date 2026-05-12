import requests

# 测试登录API返回的数据结构
login_data = {'username': '13800000001', 'password': 'admin123'}
r = requests.post('http://localhost:30001/api/v1/auth/login', data=login_data)
print('登录状态:', r.status_code)
print('返回数据:', r.text)
