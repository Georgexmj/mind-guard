import requests
import json

# 测试登录流程
print("=== 测试登录流程 ===")

# 先登录获取token
login_data = {'username': '13800000001', 'password': 'admin123'}
r = requests.post('http://localhost:30001/api/v1/auth/login', data=login_data)
print(f"登录状态: {r.status_code}")

if r.status_code == 200:
    response = r.json()
    print(f"用户角色: {response['user']['role']}")
    print(f"用户名: {response['user']['name']}")
    print(f"token长度: {len(response['access_token'])}")
    
    # 测试使用token访问受保护的路由
    headers = {'Authorization': f'Bearer {response["access_token"]}'}
    r = requests.get('http://localhost:30001/api/v1/users/elders', headers=headers)
    print(f"\n访问老人列表状态: {r.status_code}")
    if r.status_code == 200:
        elders = r.json()
        print(f"老人数量: {len(elders)}")
        print("登录流程正常！")
    else:
        print(f"访问失败: {r.text}")
else:
    print(f"登录失败: {r.text}")
