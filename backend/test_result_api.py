import requests

# 使用admin登录（手机号）
login_data = {'username': '13800000001', 'password': 'admin123'}
r = requests.post('http://localhost:8000/api/v1/auth/login', data=login_data)
if r.status_code == 200:
    token = r.json().get('access_token')
    headers = {'Authorization': 'Bearer ' + token}
    
    # 获取评估结果
    try:
        r = requests.get('http://localhost:8000/api/v1/assessments/sessions/76/result', headers=headers)
        print('API status:', r.status_code)
        print('Response:', r.text[:2000])
        
        # 检查是否有详细错误信息
        if r.status_code == 500:
            print('\n--- Response headers ---')
            for key, value in r.headers.items():
                print(f'{key}: {value}')
    except Exception as e:
        print('Exception:', str(e))
else:
    print('Login failed:', r.status_code, r.text)