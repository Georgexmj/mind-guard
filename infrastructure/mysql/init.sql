-- ============================================================
-- 基于多模态交互的社区老年认知障碍早期筛查与干预系统
-- 数据库初始化脚本
-- 数据库：MySQL 8.0
-- 版本：v1.0 | 2026-03
-- ============================================================

CREATE DATABASE IF NOT EXISTS cognitive_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE cognitive_db;

-- ============================================================
-- 1. 社区信息表
-- ============================================================
CREATE TABLE IF NOT EXISTS communities (
    id          BIGINT          NOT NULL AUTO_INCREMENT COMMENT '主键',
    name        VARCHAR(100)    NOT NULL COMMENT '社区名称',
    province    VARCHAR(20)     NOT NULL COMMENT '省份',
    city        VARCHAR(50)     NOT NULL COMMENT '城市',
    district    VARCHAR(50)     NOT NULL COMMENT '区/县',
    address     TEXT            COMMENT '详细地址',
    longitude   DECIMAL(10,7)   COMMENT '经度（GIS可视化）',
    latitude    DECIMAL(10,7)   COMMENT '纬度（GIS可视化）',
    elder_count INT             NOT NULL DEFAULT 0 COMMENT '注册老人数量',
    manager_id  BIGINT          COMMENT '负责管理员user_id（循环外键，后置添加）',
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='社区信息表';

-- ============================================================
-- 2. 用户主表
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id                  BIGINT          NOT NULL AUTO_INCREMENT COMMENT '主键',
    uuid                VARCHAR(36)     NOT NULL COMMENT '对外UUID（唯一标识）',
    phone_encrypted     VARCHAR(255)    COMMENT '手机号（AES-256加密存储）',
    name                VARCHAR(50)     NOT NULL COMMENT '真实姓名',
    birth_date          DATE            NOT NULL COMMENT '出生日期',
    gender              TINYINT         NOT NULL COMMENT '0:女 1:男',
    education_years     TINYINT         NOT NULL DEFAULT 0 COMMENT '受教育年限（0=文盲，用于量表评分校正）',
    role                ENUM('elder','family','doctor','admin') NOT NULL COMMENT '用户角色',
    community_id        BIGINT          COMMENT '所属社区ID',
    face_embedding      BLOB            COMMENT '人脸特征向量（加密，用于人脸登录）',
    voice_print         BLOB            COMMENT '声纹特征（用于声纹登录）',
    is_active           TINYINT         NOT NULL DEFAULT 1 COMMENT '账号是否启用',
    last_login_at       DATETIME        COMMENT '最后登录时间',
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
    updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '信息更新时间',
    deleted_at          DATETIME        COMMENT '软删除时间（非空表示已注销）',
    PRIMARY KEY (id),
    UNIQUE KEY uk_uuid (uuid),
    UNIQUE KEY uk_phone (phone_encrypted),
    KEY idx_community (community_id),
    KEY idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户主表';

-- 添加社区管理员外键
ALTER TABLE communities ADD CONSTRAINT fk_community_manager
    FOREIGN KEY (manager_id) REFERENCES users(id) ON DELETE SET NULL;

-- ============================================================
-- 3. 家属-老人绑定关系表
-- ============================================================
CREATE TABLE IF NOT EXISTS user_relationships (
    id              BIGINT          NOT NULL AUTO_INCREMENT COMMENT '主键',
    elder_id        BIGINT          NOT NULL COMMENT '老年用户ID',
    family_id       BIGINT          NOT NULL COMMENT '家属用户ID',
    relationship    VARCHAR(20)     NOT NULL COMMENT '关系：子女/配偶/兄弟姐妹/其他',
    notify_level    TINYINT         NOT NULL DEFAULT 1 COMMENT '通知级别：0=不通知 1=高危通知 2=全部通知',
    is_primary      TINYINT         NOT NULL DEFAULT 0 COMMENT '是否主要联系人',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '绑定时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_elder_family (elder_id, family_id),
    CONSTRAINT fk_rel_elder  FOREIGN KEY (elder_id)  REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_rel_family FOREIGN KEY (family_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='家属-老人绑定关系表';

-- ============================================================
-- 4. 题库表
-- ============================================================
CREATE TABLE IF NOT EXISTS question_bank (
    id                  BIGINT          NOT NULL AUTO_INCREMENT COMMENT '主键',
    cognitive_domain    ENUM('memory','attention','executive','language','visuospatial','orientation') NOT NULL COMMENT '认知域',
    scale_type          ENUM('mmse','moca','custom') NOT NULL COMMENT '量表类型',
    question_type       ENUM('single_choice','voice_answer','drawing','sequence','calculation','image_naming') NOT NULL COMMENT '题目类型',
    difficulty          DECIMAL(3,2)    NOT NULL DEFAULT 0.00 COMMENT 'IRT难度参数b（-3.00~3.00）',
    discrimination      DECIMAL(3,2)    NOT NULL DEFAULT 1.00 COMMENT 'IRT区分度参数a（>0）',
    content_json        JSON            NOT NULL COMMENT '题目内容（支持多媒体）',
    scoring_rule_json   JSON            NOT NULL COMMENT '评分规则',
    time_limit_sec      SMALLINT        NOT NULL DEFAULT 60 COMMENT '建议作答时限（秒）',
    tags                VARCHAR(200)    COMMENT '标签（逗号分隔）',
    is_active           TINYINT         NOT NULL DEFAULT 1 COMMENT '是否启用',
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    KEY idx_domain_type (cognitive_domain, question_type),
    KEY idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='题库';

-- ============================================================
-- 5. 评估会话主表
-- ============================================================
CREATE TABLE IF NOT EXISTS assessment_sessions (
    id                  BIGINT          NOT NULL AUTO_INCREMENT COMMENT '主键',
    session_uuid        VARCHAR(36)     NOT NULL COMMENT '会话UUID',
    user_id             BIGINT          NOT NULL COMMENT '参与评估的老人ID',
    operator_id         BIGINT          COMMENT '辅助操作医护人员ID（可空）',
    assessment_type     ENUM('screening','full','followup') NOT NULL COMMENT '评估类型',
    status              ENUM('in_progress','completed','abandoned','analyzing') NOT NULL DEFAULT 'in_progress' COMMENT '会话状态',
    started_at          DATETIME        NOT NULL COMMENT '评估开始时间',
    completed_at        DATETIME        COMMENT '评估完成时间',
    total_duration      INT             COMMENT '总用时（秒）',
    device_type         VARCHAR(20)     COMMENT '设备类型：tablet/phone/web',
    device_os           VARCHAR(30)     COMMENT '操作系统版本',
    ai_task_id          VARCHAR(64)     COMMENT 'Celery任务ID（查询AI分析进度）',
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_session_uuid (session_uuid),
    KEY idx_user_time (user_id, started_at DESC),
    KEY idx_status (status),
    CONSTRAINT fk_session_user     FOREIGN KEY (user_id)     REFERENCES users(id),
    CONSTRAINT fk_session_operator FOREIGN KEY (operator_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='评估会话主表';

-- ============================================================
-- 6. 评估综合结果表
-- ============================================================
CREATE TABLE IF NOT EXISTS assessment_results (
    id                  BIGINT          NOT NULL AUTO_INCREMENT COMMENT '主键',
    session_id          BIGINT          NOT NULL COMMENT '评估会话ID（唯一）',
    mmse_score          TINYINT         COMMENT 'MMSE量表得分（0~30，NULL表示未测）',
    moca_score          TINYINT         COMMENT 'MoCA量表得分（0~30，NULL表示未测）',
    cognitive_score     DECIMAL(5,2)    NOT NULL COMMENT 'AI综合认知评分（0~100）',
    risk_level          ENUM('low','medium','high','very_high') NOT NULL COMMENT '风险等级',
    risk_probability    DECIMAL(4,3)    NOT NULL COMMENT '认知障碍概率（0.000~1.000）',
    classification      ENUM('NC','MCI','mild_AD','uncertain') NOT NULL COMMENT '分类结果：正常/轻度认知障碍/轻度AD/不确定',
    confidence          DECIMAL(4,3)    NOT NULL COMMENT '分类置信度（0.000~1.000）',
    memory_score        DECIMAL(5,2)    COMMENT '记忆域得分（0~100）',
    attention_score     DECIMAL(5,2)    COMMENT '注意域得分（0~100）',
    executive_score     DECIMAL(5,2)    COMMENT '执行功能域得分（0~100）',
    language_score      DECIMAL(5,2)    COMMENT '语言域得分（0~100）',
    visuospatial_score  DECIMAL(5,2)    COMMENT '视空间域得分（0~100）',
    orientation_score   DECIMAL(5,2)    COMMENT '定向力域得分（0~100）',
    shap_values_json    JSON            COMMENT 'SHAP特征贡献度（可解释性）',
    ai_analysis_json    JSON            COMMENT 'AI完整分析输出',
    report_pdf_path     VARCHAR(255)    COMMENT 'MinIO中PDF报告路径',
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '结果生成时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_session (session_id),
    KEY idx_risk_level (risk_level),
    KEY idx_classification (classification),
    CONSTRAINT fk_result_session FOREIGN KEY (session_id) REFERENCES assessment_sessions(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='评估综合结果表';

-- ============================================================
-- 7. 多模态原始数据记录表
-- ============================================================
CREATE TABLE IF NOT EXISTS modality_data (
    id                  BIGINT          NOT NULL AUTO_INCREMENT COMMENT '主键',
    session_id          BIGINT          NOT NULL COMMENT '所属评估会话ID',
    modality_type       ENUM('voice','face_video','handwriting','behavior','questionnaire') NOT NULL COMMENT '模态类型',
    task_name           VARCHAR(50)     NOT NULL COMMENT '任务名称（如picture_description/clock_drawing）',
    file_path           VARCHAR(255)    COMMENT 'MinIO对象路径（音视频/图片文件）',
    raw_features_json   JSON            COMMENT '提取的特征向量（小体积）或MongoDB引用ID',
    quality_score       DECIMAL(3,2)    COMMENT '数据质量评分（0.00~1.00，<0.6需重采）',
    processing_status   ENUM('pending','processing','done','failed') NOT NULL DEFAULT 'pending' COMMENT '处理状态',
    error_message       TEXT            COMMENT '处理失败原因',
    duration_ms         INT             COMMENT '录音/录像时长（毫秒）',
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
    PRIMARY KEY (id),
    KEY idx_session_modality (session_id, modality_type),
    KEY idx_processing_status (processing_status),
    CONSTRAINT fk_modality_session FOREIGN KEY (session_id) REFERENCES assessment_sessions(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='多模态原始数据记录表';

-- ============================================================
-- 8. 题目作答明细表
-- ============================================================
CREATE TABLE IF NOT EXISTS assessment_questions (
    id                  BIGINT          NOT NULL AUTO_INCREMENT COMMENT '主键',
    session_id          BIGINT          NOT NULL COMMENT '所属评估会话ID',
    question_id         BIGINT          NOT NULL COMMENT '题目ID（引用question_bank）',
    question_order      TINYINT         NOT NULL COMMENT '本次评估中的题目序号',
    answer_value        JSON            COMMENT '作答内容（JSON，结构因题型而异）',
    is_correct          TINYINT         COMMENT '0:错误 1:正确 NULL:开放题/待AI评分',
    ai_score            DECIMAL(4,2)    COMMENT 'AI评分（用于手写/语音开放题，0~100）',
    response_time_ms    INT             NOT NULL DEFAULT 0 COMMENT '答题用时（毫秒）',
    revision_count      TINYINT         NOT NULL DEFAULT 0 COMMENT '答题中途修改次数',
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作答时间',
    PRIMARY KEY (id),
    KEY idx_session_order (session_id, question_order),
    KEY idx_question (question_id),
    CONSTRAINT fk_qa_session  FOREIGN KEY (session_id)  REFERENCES assessment_sessions(id),
    CONSTRAINT fk_qa_question FOREIGN KEY (question_id) REFERENCES question_bank(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='题目作答明细表';

-- ============================================================
-- 9. 干预计划表
-- ============================================================
CREATE TABLE IF NOT EXISTS intervention_plans (
    id              BIGINT          NOT NULL AUTO_INCREMENT COMMENT '主键',
    user_id         BIGINT          NOT NULL COMMENT '目标老人ID',
    creator_id      BIGINT          NOT NULL COMMENT '制定者用户ID（系统推荐时为0）',
    source          ENUM('ai_recommend','doctor_manual') NOT NULL DEFAULT 'ai_recommend' COMMENT '方案来源',
    plan_type       ENUM('cognitive_training','music','exercise','social','lifestyle','medication') NOT NULL COMMENT '干预类型',
    priority        TINYINT         NOT NULL DEFAULT 3 COMMENT '优先级 1(低)~5(高)',
    title           VARCHAR(100)    NOT NULL COMMENT '方案标题',
    description     TEXT            COMMENT '详细描述',
    start_date      DATE            NOT NULL COMMENT '开始日期',
    end_date        DATE            COMMENT '结束日期（NULL表示长期）',
    frequency       VARCHAR(50)     COMMENT '频率描述（如每天10分钟）',
    target_domain   VARCHAR(100)    COMMENT '针对的认知域（逗号分隔）',
    content_json    JSON            COMMENT '具体内容（游戏ID/视频链接等）',
    status          ENUM('active','completed','abandoned','paused') NOT NULL DEFAULT 'active' COMMENT '计划状态',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    KEY idx_user_status (user_id, status),
    KEY idx_plan_type (plan_type),
    CONSTRAINT fk_plan_user    FOREIGN KEY (user_id)    REFERENCES users(id),
    CONSTRAINT fk_plan_creator FOREIGN KEY (creator_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='干预计划表';

-- ============================================================
-- 10. 干预执行记录表
-- ============================================================
CREATE TABLE IF NOT EXISTS intervention_records (
    id                  BIGINT          NOT NULL AUTO_INCREMENT COMMENT '主键',
    plan_id             BIGINT          NOT NULL COMMENT '所属干预计划ID',
    user_id             BIGINT          NOT NULL COMMENT '执行用户ID',
    executed_at         DATETIME        NOT NULL COMMENT '执行时间',
    duration_sec        INT             COMMENT '实际执行时长（秒）',
    completion_rate     DECIMAL(3,2)    COMMENT '完成度（0.00~1.00）',
    feedback_score      TINYINT         COMMENT '用户满意度评分（1~5星）',
    notes               TEXT            COMMENT '备注',
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    PRIMARY KEY (id),
    KEY idx_plan (plan_id),
    KEY idx_user_time (user_id, executed_at DESC),
    CONSTRAINT fk_record_plan FOREIGN KEY (plan_id) REFERENCES intervention_plans(id),
    CONSTRAINT fk_record_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='干预执行记录表';

-- ============================================================
-- 初始化数据
-- ============================================================

-- 插入示例社区
INSERT INTO communities (name, province, city, district, address, longitude, latitude)
VALUES
('阳光花苑社区', '湖南省', '张家界市', '永定区', '解放路街道阳光花苑小区', 110.4784, 29.1276),
('桂花园社区',   '湖南省', '张家界市', '永定区', '民族路街道桂花园社区',   110.4815, 29.1244);

-- 插入系统管理员账号（密码：admin123，实际使用时改为bcrypt哈希）
INSERT INTO users (uuid, name, birth_date, gender, education_years, role, is_active)
VALUES (UUID(), '系统管理员', '1990-01-01', 1, 16, 'admin', 1);

-- 插入示例题库（MMSE定向力题）
INSERT INTO question_bank (cognitive_domain, scale_type, question_type, difficulty, discrimination, content_json, scoring_rule_json, time_limit_sec, tags)
VALUES
(
    'orientation', 'mmse', 'voice_answer', -1.50, 1.20,
    '{"stem": "请问今天是几月几日？", "guide": "（请用语音回答）", "answer_mode": "voice"}',
    '{"type": "date_check", "tolerance_days": 2, "score": 1}',
    30, '定向力,日期'
),
(
    'orientation', 'mmse', 'voice_answer', -1.00, 1.30,
    '{"stem": "请问现在是哪一年？", "guide": "（请用语音回答年份）", "answer_mode": "voice"}',
    '{"type": "year_check", "tolerance": 0, "score": 1}',
    20, '定向力,年份'
),
(
    'memory', 'mmse', 'voice_answer', 0.50, 1.50,
    '{"stem": "请记住这三个词：苹果、汽车、诚信。稍后我会请您回忆。", "guide": "（现在请重复这三个词）", "answer_mode": "voice", "words": ["苹果","汽车","诚信"]}',
    '{"type": "word_recall", "words": ["苹果","汽车","诚信"], "partial_credit": true, "score_per_word": 1}',
    30, '记忆,即时回忆'
),
(
    'attention', 'mmse', 'calculation', 0.80, 1.40,
    '{"stem": "请从100开始，每次减去7，说出结果。", "guide": "（请连续减5次）", "answer_mode": "voice", "start": 100, "step": 7, "count": 5}',
    '{"type": "serial_subtraction", "answers": [93,86,79,72,65], "tolerance": 0, "score_per_correct": 1}',
    60, '注意力,计算'
),
(
    'visuospatial', 'moca', 'drawing', 1.20, 1.60,
    '{"stem": "请在圆圈内画一个时钟，写上全部数字，并把时间拨到十点十分。", "guide": "（请在触屏上绘制）", "answer_mode": "drawing"}',
    '{"type": "clock_drawing", "criteria": ["circle_closed","numbers_complete","hands_correct"], "score": 3}',
    120, '视空间,时钟绘图,执行功能'
);

-- ============================================================
-- 完成
-- ============================================================
SELECT '数据库初始化完成！' AS message;
SELECT table_name, table_comment
FROM information_schema.tables
WHERE table_schema = 'cognitive_db'
ORDER BY table_name;
