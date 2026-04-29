# 基于多模态交互的社区老年认知障碍早期筛查与干预系统

> MindGuard，面向社区老年人的认知障碍早筛、评估报告、干预随访与预警协同系统。

## 项目概述

本项目围绕社区 60 岁以上老年人，提供“老人端小程序评估 + 医生/管理员 Web 管理端 + 后端 AI 分析与干预闭环”的完整演示系统。当前代码已实现账号认证、角色权限、评估会话、题库管理、异步分析、报告查询、干预计划、干预打卡、依从性预警、通知提醒、RAG 知识库和 Docker 部署基础设施。

系统当前定位为竞赛与原型验证系统：筛查结果用于早期风险提示、家庭沟通和社区医生随访辅助，不替代医院临床诊断。

## 当前代码结构

```text
.
├── backend/          # FastAPI 后端、Celery 任务、SQLAlchemy 模型、AI/规则推理服务
├── web-admin/        # React 18 + TypeScript + Ant Design 管理端
├── miniprogram/      # UniApp + Vue 3 微信小程序老人端
├── data/             # 合成多模态训练数据、公开数据拉取脚本、训练清单
├── docs/             # 需求、架构、接口、部署、开发、商业计划等文档
├── infrastructure/   # 辅助 docker-compose 与 MySQL 初始化脚本
├── nginx/            # 开发/生产 Nginx 配置与证书目录
├── docker-compose.yml
├── .env.example
├── QUICKSTART.md
└── CLAUDE.md
```

## 核心功能

| 模块 | 当前实现 |
| --- | --- |
| 账号与权限 | JWT 登录，老人、家属、医生、管理员四类角色，家属绑定老人，微信 openid 绑定 |
| 认知评估 | 创建/暂停/恢复/删除评估会话，题目分发，作答提交，语音文件上传，完成后触发异步分析 |
| AI 分析 | 支持 `rule`、`deep`、`hybrid` 三种策略；深度模型 checkpoint 缺失时可回退规则模型 |
| 报告输出 | 评估结果、家庭可读报告、医生 PDF 报告、批量导出、趋势数据 |
| 医生工作台 | 总览统计、月度趋势、风险分布、高风险列表、干预工单队列 |
| 干预闭环 | Top5 推荐、医生建计划、老人每日打卡、依从性预警工单、提醒分发 |
| 通知提醒 | 站内通知、未读数、已读处理；微信订阅消息配置项已预留 |
| RAG 知识库 | 知识条目管理、索引重建、检索接口，用于干预建议和解释材料 |

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 后端 | Python 3.11, FastAPI, SQLAlchemy, Pydantic, Celery, Redis |
| AI/数据 | PyTorch, scikit-learn, LightGBM, FAISS, ReportLab, 合成多模态数据集 |
| Web 管理端 | React 18, TypeScript, Vite, Ant Design 5, ECharts, Zustand, Axios |
| 小程序 | UniApp, Vue 3, Pinia, 微信录音与 Canvas 能力 |
| 存储与部署 | MySQL, Redis, MinIO, InfluxDB, MongoDB, Docker Compose, Nginx |

## 快速启动

推荐先复制环境变量模板：

```bash
cp .env.example .env
```

Docker 演示环境：

```bash
docker compose up -d --build
docker compose ps
```

默认访问地址以 `.env.example` 为准：

| 服务 | 地址 |
| --- | --- |
| Web 管理端 | http://localhost:30000 |
| 后端 Swagger | http://localhost:8000/docs |
| MinIO Console | http://localhost:9001 |

本地开发步骤见 [QUICKSTART.md](QUICKSTART.md)。

## 演示账号

由 `backend/app/initial_data.py` 初始化：

| 角色 | 手机号 | 密码 |
| --- | --- | --- |
| 管理员 | `13800000001` | `admin123` |
| 医生 | `13800000002` | `doctor123` |
| 老人 | `13800000003` | `elder123` |

## 文档导航

| 文档 | 说明 |
| --- | --- |
| [docs/文档导航.md](docs/文档导航.md) | 全部文档索引、现状校准和阅读顺序 |
| [docs/开发/项目结构.md](docs/开发/项目结构.md) | 当前真实目录结构 |
| [docs/接口/接口设计.md](docs/接口/接口设计.md) | 当前后端路由与接口口径 |
| [docs/系统架构/系统架构设计.md](docs/系统架构/系统架构设计.md) | 运行时架构与业务流程 |
| [docs/系统架构/数据库设计.md](docs/系统架构/数据库设计.md) | ORM 表结构与核心关系 |
| [docs/部署/部署说明.md](docs/部署/部署说明.md) | Docker、本地开发、生产部署说明 |
| [docs/人工智能/算法设计.md](docs/人工智能/算法设计.md) | 算法方案与当前工程落地边界 |
| [docs/需求/功能清单_进度版_2026-04-01.md](docs/需求/功能清单_进度版_2026-04-01.md) | 功能进度口径 |
| [docs/商业计划](docs/商业计划) | 参赛商业计划章节 |

## 重要说明

- 当前后端 API 返回 FastAPI/Pydantic 原生响应体，并非统一 `{code,message,data}` 包装。
- 当前没有独立 `ai-engine/` 服务目录，深度模型推理集成在 `backend/app/services/deep_model_service.py`。
- 当前没有独立 `/api/v1/modality` 或 `/api/v1/reports` 路由；音频上传、报告导出和趋势查询在 `/api/v1/assessments` 下提供。
- 生产环境必须替换 `.env` 中的 `SECRET_KEY`、数据库密码、MinIO 密码和微信配置。

*文档修订：2026-04-29*
