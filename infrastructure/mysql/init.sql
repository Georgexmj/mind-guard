-- ============================================================
-- MindGuard 数据库初始化脚本（与当前 ORM 模型对齐）
-- ============================================================

CREATE DATABASE IF NOT EXISTS cognitive_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE cognitive_db;

SET NAMES utf8mb4;

-- 1) 社区
CREATE TABLE IF NOT EXISTS communities (
  id           INT PRIMARY KEY AUTO_INCREMENT,
  name         VARCHAR(200) NOT NULL,
  province     VARCHAR(50)  NOT NULL,
  city         VARCHAR(50)  NOT NULL,
  district     VARCHAR(50)  NULL,
  address      VARCHAR(500) NULL,
  elder_count  INT NOT NULL DEFAULT 0,
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_communities_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2) 用户
CREATE TABLE IF NOT EXISTS users (
  id             INT PRIMARY KEY AUTO_INCREMENT,
  uuid           VARCHAR(36) NOT NULL,
  phone          VARCHAR(20) NOT NULL,
  name           VARCHAR(100) NOT NULL,
  birth_date     DATE NULL,
  gender         VARCHAR(10) NULL,
  education_years INT NULL,
  role           ENUM('elder','family','doctor','admin') NOT NULL DEFAULT 'elder',
  community_id   INT NULL,
  password_hash  VARCHAR(255) NOT NULL,
  is_active      TINYINT(1) NOT NULL DEFAULT 1,
  last_login_at  DATETIME NULL,
  created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_users_uuid (uuid),
  UNIQUE KEY uk_users_phone (phone),
  INDEX idx_users_role (role),
  INDEX idx_users_community (community_id),
  CONSTRAINT fk_users_community FOREIGN KEY (community_id) REFERENCES communities(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3) 家属关系
CREATE TABLE IF NOT EXISTS user_relationships (
  id            INT PRIMARY KEY AUTO_INCREMENT,
  elder_id      INT NOT NULL,
  family_id     INT NOT NULL,
  relationship  VARCHAR(50) NOT NULL,
  notify_level  INT NOT NULL DEFAULT 1,
  is_primary    TINYINT(1) NOT NULL DEFAULT 0,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_user_relationships_pair (elder_id, family_id),
  INDEX idx_user_relationships_elder (elder_id),
  INDEX idx_user_relationships_family (family_id),
  CONSTRAINT fk_user_relationships_elder FOREIGN KEY (elder_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_user_relationships_family FOREIGN KEY (family_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4) 微信绑定
CREATE TABLE IF NOT EXISTS wechat_bindings (
  id            INT PRIMARY KEY AUTO_INCREMENT,
  user_id       INT NOT NULL,
  openid        VARCHAR(100) NOT NULL,
  unionid       VARCHAR(100) NULL,
  is_active     TINYINT(1) NOT NULL DEFAULT 1,
  last_sent_at  DATETIME NULL,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_wechat_bindings_openid (openid),
  INDEX idx_wechat_bindings_user (user_id),
  INDEX idx_wechat_bindings_unionid (unionid),
  CONSTRAINT fk_wechat_bindings_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5) 题库（ORM: questions）
CREATE TABLE IF NOT EXISTS questions (
  id            INT PRIMARY KEY AUTO_INCREMENT,
  domain        ENUM('memory','orientation','language','attention','visuospatial','executive') NOT NULL,
  q_type        ENUM('choice','voice','drawing','scale') NOT NULL,
  content       TEXT NOT NULL,
  options       JSON NULL,
  correct_answer VARCHAR(500) NULL,
  difficulty    FLOAT NOT NULL DEFAULT 0.5,
  irt_a         FLOAT NOT NULL DEFAULT 1.0,
  irt_b         FLOAT NOT NULL DEFAULT 0.0,
  is_active     TINYINT(1) NOT NULL DEFAULT 1,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_questions_domain (domain),
  INDEX idx_questions_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6) 评估会话
CREATE TABLE IF NOT EXISTS assessment_sessions (
  id            INT PRIMARY KEY AUTO_INCREMENT,
  user_id       INT NOT NULL,
  status        ENUM('pending','in_progress','completed','failed') NOT NULL DEFAULT 'pending',
  started_at    DATETIME NULL,
  completed_at  DATETIME NULL,
  task_id       VARCHAR(255) NULL,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_assessment_sessions_user (user_id),
  INDEX idx_assessment_sessions_status (status),
  CONSTRAINT fk_assessment_sessions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7) 作答记录（ORM: assessment_responses）
CREATE TABLE IF NOT EXISTS assessment_responses (
  id              INT PRIMARY KEY AUTO_INCREMENT,
  session_id      INT NOT NULL,
  question_id     INT NOT NULL,
  answer_text     TEXT NULL,
  answer_data     JSON NULL,
  reaction_time_ms INT NULL,
  is_correct      TINYINT(1) NULL,
  score           FLOAT NULL,
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_assessment_responses_once (session_id, question_id),
  INDEX idx_assessment_responses_session (session_id),
  INDEX idx_assessment_responses_question (question_id),
  CONSTRAINT fk_assessment_responses_session FOREIGN KEY (session_id) REFERENCES assessment_sessions(id) ON DELETE CASCADE,
  CONSTRAINT fk_assessment_responses_question FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8) 评估结果（风险枚举与 ORM 一致）
CREATE TABLE IF NOT EXISTS assessment_results (
  id             INT PRIMARY KEY AUTO_INCREMENT,
  session_id     INT NOT NULL,
  risk_level     ENUM('normal','mild_risk','high_risk') NOT NULL,
  nc_probability FLOAT NOT NULL,
  mci_probability FLOAT NOT NULL,
  ad_probability FLOAT NOT NULL,
  mmse_score     FLOAT NULL,
  domain_scores  JSON NOT NULL,
  shap_values    JSON NULL,
  recommendation TEXT NULL,
  created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_assessment_results_session (session_id),
  INDEX idx_assessment_results_risk (risk_level),
  CONSTRAINT fk_assessment_results_session FOREIGN KEY (session_id) REFERENCES assessment_sessions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9) 干预计划
CREATE TABLE IF NOT EXISTS intervention_plans (
  id            INT PRIMARY KEY AUTO_INCREMENT,
  elder_id      INT NOT NULL,
  created_by    INT NOT NULL,
  title         VARCHAR(200) NOT NULL,
  description   TEXT NULL,
  domain_focus  VARCHAR(200) NULL,
  frequency     VARCHAR(100) NULL,
  duration_days INT NULL,
  start_date    DATE NULL,
  end_date      DATE NULL,
  status        ENUM('active','paused','completed','cancelled') NOT NULL DEFAULT 'active',
  ai_priority   FLOAT NULL,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_intervention_plans_elder (elder_id),
  CONSTRAINT fk_intervention_plans_elder FOREIGN KEY (elder_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_intervention_plans_creator FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10) 干预执行记录
CREATE TABLE IF NOT EXISTS intervention_records (
  id            INT PRIMARY KEY AUTO_INCREMENT,
  plan_id       INT NOT NULL,
  elder_id      INT NOT NULL,
  record_date   DATE NOT NULL,
  completed     TINYINT(1) NOT NULL DEFAULT 0,
  duration_min  INT NULL,
  notes         TEXT NULL,
  mood_score    INT NULL,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_intervention_records_plan (plan_id),
  INDEX idx_intervention_records_elder (elder_id),
  CONSTRAINT fk_intervention_records_plan FOREIGN KEY (plan_id) REFERENCES intervention_plans(id) ON DELETE CASCADE,
  CONSTRAINT fk_intervention_records_elder FOREIGN KEY (elder_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11) 依从性工单
CREATE TABLE IF NOT EXISTS intervention_adherence_tickets (
  id                         INT PRIMARY KEY AUTO_INCREMENT,
  plan_id                    INT NOT NULL,
  elder_id                   INT NOT NULL,
  status                     ENUM('open','in_progress','resolved','ignored') NOT NULL DEFAULT 'open',
  owner_doctor_id            INT NULL,
  reminder_at                DATETIME NULL,
  followup_note              TEXT NULL,
  consecutive_missed_days    INT NOT NULL DEFAULT 0,
  completion_rate            FLOAT NOT NULL DEFAULT 0,
  latest_interruption_reason VARCHAR(300) NULL,
  risk_level                 VARCHAR(30) NULL,
  resolved_at                DATETIME NULL,
  last_notified_at           DATETIME NULL,
  created_at                 DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at                 DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_adherence_tickets_plan (plan_id),
  INDEX idx_adherence_tickets_elder (elder_id),
  INDEX idx_adherence_tickets_status (status),
  INDEX idx_adherence_tickets_owner (owner_doctor_id),
  CONSTRAINT fk_adherence_tickets_plan FOREIGN KEY (plan_id) REFERENCES intervention_plans(id) ON DELETE CASCADE,
  CONSTRAINT fk_adherence_tickets_elder FOREIGN KEY (elder_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_adherence_tickets_owner FOREIGN KEY (owner_doctor_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12) 通知
CREATE TABLE IF NOT EXISTS notifications (
  id                INT PRIMARY KEY AUTO_INCREMENT,
  user_id           INT NOT NULL,
  session_id        INT NULL,
  notification_type ENUM('assessment_completed','high_risk_alert','system_message') NOT NULL,
  title             VARCHAR(200) NOT NULL,
  content           TEXT NOT NULL,
  risk_level        VARCHAR(30) NULL,
  payload           JSON NULL,
  is_read           TINYINT(1) NOT NULL DEFAULT 0,
  read_at           DATETIME NULL,
  created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_notifications_user (user_id),
  INDEX idx_notifications_session (session_id),
  INDEX idx_notifications_type (notification_type),
  CONSTRAINT fk_notifications_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_notifications_session FOREIGN KEY (session_id) REFERENCES assessment_sessions(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 13) RAG 知识条目
CREATE TABLE IF NOT EXISTS rag_knowledge_items (
  id            INT PRIMARY KEY AUTO_INCREMENT,
  kb_type       ENUM('rule','intervention','template','faq') NOT NULL,
  title         VARCHAR(255) NOT NULL,
  content       TEXT NOT NULL,
  tags          VARCHAR(255) NULL,
  metadata_json JSON NULL,
  is_active     TINYINT(1) NOT NULL DEFAULT 1,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_rag_knowledge_items_type (kb_type),
  INDEX idx_rag_knowledge_items_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 基础社区种子（账号和题库建议执行: python -m app.initial_data）
INSERT INTO communities (name, province, city, district, address, elder_count)
SELECT '幸福社区', '湖南省', '张家界市', '永定区', '张家界市永定区解放路街道幸福社区', 0
WHERE NOT EXISTS (SELECT 1 FROM communities WHERE name = '幸福社区');

SELECT 'ORM 对齐初始化完成' AS message;
