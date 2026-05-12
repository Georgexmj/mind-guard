from sqlalchemy import create_engine, text
import random
from datetime import datetime, timezone

engine = create_engine('sqlite:///./cognitive.db')

# 定义风险等级分布（根据已有数据的模式）
risk_levels = ['mild_risk', 'moderate_risk', 'high_risk']

# 为每个老人定义风险等级分布权重
elder_risk_weights = {
    3: {'mild_risk': 0.2, 'moderate_risk': 0.3, 'high_risk': 0.5},   # 李奶奶 - 倾向高风险
    6: {'mild_risk': 0.5, 'moderate_risk': 0.3, 'high_risk': 0.2},   # 赵奶奶 - 倾向低风险
    9: {'mild_risk': 0.2, 'moderate_risk': 0.3, 'high_risk': 0.5},   # 孙爷爷 - 倾向高风险
    10: {'mild_risk': 0.4, 'moderate_risk': 0.4, 'high_risk': 0.2},  # 周奶奶 - 均衡
    5: {'mild_risk': 0.3, 'moderate_risk': 0.4, 'high_risk': 0.3},   # 王爷爷 - 均衡
}

def get_random_risk_level(elder_id):
    weights = elder_risk_weights.get(elder_id, {'mild_risk': 0.33, 'moderate_risk': 0.34, 'high_risk': 0.33})
    return random.choices(list(weights.keys()), weights=list(weights.values()))[0]

def generate_mmse_score(risk_level):
    """根据风险等级生成MMSE分数"""
    if risk_level == 'mild_risk':
        return random.randint(20, 26)  # 轻度认知障碍范围
    elif risk_level == 'moderate_risk':
        return random.randint(10, 19)  # 中度认知障碍范围
    elif risk_level == 'high_risk':
        return random.randint(0, 9)     # 重度认知障碍范围
    return random.randint(24, 30)

def generate_probabilities(risk_level):
    """根据风险等级生成概率值"""
    base_ad_prob = {'mild_risk': 0.2, 'moderate_risk': 0.5, 'high_risk': 0.8}[risk_level]
    return {
        'nc': round(0.1 + random.random() * 0.2, 4),
        'mci': round(0.2 + random.random() * 0.3, 4),
        'ad': round(base_ad_prob + random.random() * 0.15, 4)
    }

with engine.connect() as conn:
    # 获取没有评估结果的会话
    result = conn.execute(text('''
        SELECT s.id, s.user_id, s.completed_at
        FROM assessment_sessions s
        LEFT JOIN assessment_results r ON s.id = r.session_id
        WHERE s.status = "completed" AND r.id IS NULL
    '''))
    
    sessions = [{'id': row[0], 'user_id': row[1], 'completed_at': row[2]} for row in result]
    
    print(f"找到 {len(sessions)} 个没有评估结果的会话")
    
    for session in sessions:
        risk_level = get_random_risk_level(session['user_id'])
        mmse_score = generate_mmse_score(risk_level)
        probs = generate_probabilities(risk_level)
        completed_at = session['completed_at']
        
        # 生成领域分数
        domain_scores = {
            'memory': round(0.3 + random.random() * 0.4, 4),
            'attention': round(0.3 + random.random() * 0.4, 4),
            'language': round(0.3 + random.random() * 0.4, 4),
            'executive': round(0.3 + random.random() * 0.4, 4),
            'visuospatial': round(0.3 + random.random() * 0.4, 4),
            'orientation': round(0.3 + random.random() * 0.4, 4)
        }
        
        # 插入评估结果
        conn.execute(text('''
            INSERT INTO assessment_results 
            (session_id, risk_level, nc_probability, mci_probability, ad_probability, 
             mmse_score, domain_scores, created_at)
            VALUES (:session_id, :risk_level, :nc_prob, :mci_prob, :ad_prob, 
                    :mmse, :domain_scores, :created)
        '''), {
            'session_id': session['id'],
            'risk_level': risk_level,
            'nc_prob': probs['nc'],
            'mci_prob': probs['mci'],
            'ad_prob': probs['ad'],
            'mmse': mmse_score,
            'domain_scores': str(domain_scores).replace("'", "\""),
            'created': completed_at
        })
        
        print(f"会话 {session['id']}: 风险等级={risk_level}, MMSE={mmse_score}")
    
    conn.commit()
    print("评估结果已生成完成！")