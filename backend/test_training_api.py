import requests
import time
time.sleep(2)

# 使用冯奶奶的手机号登录（ID=14，手机号=13800000014）
login_data = {'username': '13800000014', 'password': '123456'}
r = requests.post('http://localhost:30001/api/v1/auth/login', data=login_data)

if r.status_code == 200:
    token = r.json().get('access_token')
    headers = {'Authorization': 'Bearer ' + token}
    
    print('测试训练报告API（带JWT token）:')
    
    # 模拟训练数据上报
    training_data = {
        'userId': 'unknown',  # 即使是unknown，也会使用token中的用户ID
        'courseId': 'image_memory',
        'courseName': '图片记忆训练',
        'correctCount': 5,
        'totalQuestions': 5,
        'accuracy': 100,
        'completedAt': '2026-05-12T12:40:00.000Z',
        'answers': []
    }
    
    r = requests.post('http://localhost:30001/api/v1/training/report', json=training_data, headers=headers, timeout=10)
    print('状态码:', r.status_code)
    if r.status_code == 201:
        result = r.json()
        elder_id = result.get('elder_id')
        print('训练记录已创建，elder_id=' + str(elder_id))
        print('期望的elder_id=14（冯奶奶）')
        if elder_id == 14:
            print('SUCCESS: 训练记录正确关联到冯奶奶！')
        else:
            print('FAIL: 训练记录没有正确关联到冯奶奶')
    else:
        print('错误:', r.text[:500])
else:
    print('登录失败:', r.status_code, r.text[:200])