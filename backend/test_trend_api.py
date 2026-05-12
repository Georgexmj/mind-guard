import requests

# 先登录获取token（使用管理员手机号）
login_data = {'username': '13800000001', 'password': 'admin123'}
r = requests.post('http://localhost:30001/api/v1/auth/login', data=login_data)

if r.status_code == 200:
    token = r.json().get('access_token')
    headers = {'Authorization': 'Bearer ' + token}
    
    # 请求评估趋势数据
    r = requests.get('http://localhost:30001/api/v1/dashboard/monthly-trend?months=6', headers=headers)
    print('状态码:', r.status_code)
    print('响应数据:', r.json())
else:
    print('登录失败:', r.status_code, r.text)