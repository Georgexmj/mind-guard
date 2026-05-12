import requests
import traceback

# 先登录获取token
login_data = {'username': '13800000001', 'password': 'admin123'}
r = requests.post('http://localhost:30001/api/v1/auth/login', data=login_data)

if r.status_code == 200:
    token = r.json().get('access_token')
    headers = {'Authorization': 'Bearer ' + token}
    
    # 测试获取老人列表API
    print('测试获取老人列表API:')
    try:
        r = requests.get('http://localhost:30001/api/v1/users/elders?page=1&page_size=100', headers=headers)
        print(f'状态码: {r.status_code}')
        if r.status_code == 200:
            data = r.json()
            print(f'返回老人数量: {len(data)}')
            if data:
                print(f'第一个老人: {data[0]["name"]}')
        else:
            print(f'错误响应:')
            print(r.text)
    except Exception as e:
        print(f'请求异常: {e}')
        traceback.print_exc()
else:
    print('登录失败:', r.status_code, r.text)