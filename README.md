# 基于多模态交互的社区老年认知障碍早期筛查与干预系统

> 全国大学生软件创新大赛参赛项目

---

## 项目概述

本系统面向社区60岁以上老年人群体，综合运用**语音交互、视觉分析、行为监测、数字化量表**四种模态数据，构建一套智能化的认知障碍早期筛查与干预闭环系统。

**解决的核心问题：**
- 传统MMSE/MoCA量表需要专业医生面对面施测，社区覆盖率极低（全国仅约12%的高危老人接受过专业评估）
- MCI（轻度认知障碍）阶段是干预的黄金窗口期，但症状隐匿，难以早期发现
- 现有移动端筛查App模态单一（仅问卷），老年人不友好，依从性差

---

## 核心技术创新点

### 1. 跨模态注意力融合架构（技术核心）
设计了专门针对认知障碍特征异质性的**Cross-Modal Attention**机制，动态学习"记忆域→语音主导、执行功能域→手写笔迹主导"的细粒度模态-认知域对齐关系，优于简单特征拼接的早期融合方案。

### 2. 无感化游戏化评估
将评估嵌入自然对话和游戏场景，消除传统量表的"白大褂效应"。针对低教育水平（文盲/小学）老人引入受教育年限校正系数，解决传统量表的系统性偏差问题。

### 3. 被动行为生物标志物连续监测
在老年用户日常使用App过程中，持续采集**触屏运动学特征**（点击精准度、反应时间、笔迹抖动），实现无需主动配合的7×24小时认知状态监测。

### 4. 可解释AI（XAI）诊断报告
采用**SHAP值**为每次诊断输出特征贡献度，生成"本次评估主要依据：词语记忆（38%）、语音流利度（31%）、时钟绘图（18%）"的可解释报告，解决黑盒AI的医患信任问题。

### 5. 纵向MCI→AD转化风险预测
基于**LSTM**对用户历次评估数据建模认知衰退轨迹，预测未来12个月内MCI转化为AD的概率，实现真正意义的"早期干预时间窗口"识别。

### 6. 三方协同干预闭环
构建老人—家属—医生三方信息同步的量化干预闭环：医生制定方案 → 家属监督执行 → 系统评估效果 → 自动调整推荐。

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                     用户交互层                                │
│   Web管理端(React 18)  |  微信小程序(UniApp)    |  平板端    │
├─────────────────────────────────────────────────────────────┤
│                     API 网关层                                │
│          Nginx反向代理  |  JWT鉴权  |  限流熔断               │
├─────────────────────────────────────────────────────────────┤
│                     业务服务层                                │
│   用户服务 | 筛查服务 | AI分析服务 | 干预服务 | 报告服务       │
├─────────────────────────────────────────────────────────────┤
│                     AI 引擎层                                 │
│  多模态融合模型 | 风险预测模型 | 个性化推荐引擎 | NLP引擎       │
├─────────────────────────────────────────────────────────────┤
│                     数据存储层                                │
│  MySQL(业务) | Redis(缓存) | MinIO(文件) | InfluxDB(时序)     │
└─────────────────────────────────────────────────────────────┘
```

---

## 四类用户角色

| 角色 | 核心功能 | 交互方式 |
|------|----------|----------|
| **老年用户** | 参与认知评估、查看简化报告、接受干预训练 | 语音优先 + 大字体微信小程序 |
| **家属监护人** | 查看详细报告、设置提醒、参与干预计划 | 微信小程序 |
| **社区医生/护士** | 管辖老人健康档案、制定干预方案、预警处置 | Web管理端 |
| **系统管理员** | 社区数据看板、群体风险分析、系统配置 | Web管理端 |

---

## 技术栈

```
后端：      Python 3.11 + FastAPI + Celery + SQLAlchemy + Alembic
AI/ML：     PyTorch 2.1 + Transformers + scikit-learn + LightGBM
语音处理：  Whisper large-v3 + OpenSMILE + Librosa + jieba + chinese-BERT
视觉处理：  MediaPipe + OpenCV + GazeTracking + FER2013
前端Web：   React 18 + TypeScript + Ant Design 5 + ECharts 5
移动端：    UniApp + Vue 3 + Pinia + 微信原生API（wx.getRecorderManager/wx.getTextToSpeech）
数据库：    MySQL 8.0 + Redis 7.0 + MinIO + InfluxDB 2.0
部署：      Docker + Docker Compose + Nginx
```

---

## 项目文档导航

| 文档 | 路径 | 说明 |
|------|------|------|
| 系统架构设计 | [docs/architecture/system_architecture.md](docs/architecture/system_architecture.md) | 五层架构详细设计 |
| 数据库设计 | [docs/architecture/database_design.md](docs/architecture/database_design.md) | ER关系 + 表结构说明 |
| SQL初始化脚本 | [infrastructure/mysql/init.sql](infrastructure/mysql/init.sql) | 可直接执行的建表语句 |
| AI算法设计 | [docs/ai/algorithm_design.md](docs/ai/algorithm_design.md) | 多模态融合核心算法 |
| API接口文档 | [docs/api/api_design.md](docs/api/api_design.md) | REST接口完整定义 |
| 功能需求说明书 | [docs/requirements/functional_requirements.md](docs/requirements/functional_requirements.md) | 完整功能需求 |
| 功能列表清单 | [docs/requirements/feature_list.md](docs/requirements/feature_list.md) | MVP功能清单 |
| 落地实施规划 | [docs/development/implementation_roadmap.md](docs/development/implementation_roadmap.md) | 开发里程碑计划 |
| 项目目录结构 | [docs/development/project_structure.md](docs/development/project_structure.md) | 目录规范说明 |

---

## 社会价值

- 中国60岁以上老年人超**3亿**，MCI患病率约15%，潜在筛查需求约**4500万**
- MCI阶段干预成本约为AD阶段的**1/10**，早筛早干预可显著降低长期医疗负担
- 系统以社区为基本单元，单名社区医生可管辖**数百名**老年人，极大缓解医疗资源短缺
- 特别针对低教育水平农村老人优化，弥补现有量表的公平性缺口

---

## 快速启动（开发环境）

```bash
# 1. 克隆项目
git clone <repository-url>
cd cognitive-screening-system

# 2. 启动基础服务（数据库/缓存/存储）
docker-compose up -d mysql redis minio influxdb

# 3. 初始化数据库
mysql -u root -p cognitive_db < infrastructure/mysql/init.sql

# 4. 启动后端服务
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 5. 启动AI引擎
cd ai-engine
pip install -r requirements.txt
uvicorn serving.inference_server:app --port 8001

# 6. 启动Web前端
cd frontend/web-admin
npm install && npm run dev

# 7. 开发微信小程序（需安装微信开发者工具）
cd frontend/miniprogram
npm install
# 用微信开发者工具打开 frontend/miniprogram 目录
```

---

*项目持续开发中 | 全国大学生软件创新大赛参赛作品*
