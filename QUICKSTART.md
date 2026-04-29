# MindGuard 快速启动指南

本文说明如何在本地跑通后端、Web 管理端、小程序与基础设施。

## 环境要求

| 工具 | 建议版本 | 用途 |
| --- | --- | --- |
| Docker Desktop | 24+ | 一键启动 MySQL、Redis、MinIO、后端、Web、Nginx |
| Python | 3.11+ | 后端本地开发 |
| Node.js | 20+ | Web 管理端与小程序构建 |
| 微信开发者工具 | 最新版 | 小程序调试与上传 |

## 方式一：Docker 一键启动

```bash
cp .env.example .env
docker compose up -d --build
docker compose ps
docker compose logs -f backend
```

启动后访问：

| 服务 | 默认地址 |
| --- | --- |
| Web 管理端 | http://localhost:30000 |
| 后端 Swagger | http://localhost:8000/docs |
| MinIO Console | http://localhost:9001 |

停止服务：

```bash
docker compose down
```

清空数据卷后重建：

```bash
docker compose down -v
docker compose up -d --build
```

## 方式二：本地开发模式

### 1. 启动基础设施

```bash
cp .env.example .env
docker compose up -d mysql redis minio influxdb mongodb
```

### 2. 启动后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m app.initial_data
uvicorn app.main:app --reload --port 8000
```

macOS/Linux 激活虚拟环境使用：

```bash
source .venv/bin/activate
```

后端文档：http://localhost:8000/docs

### 3. 启动 Celery Worker

```bash
cd backend
.venv\Scripts\activate
celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2 -Q ai_analysis,celery
```

如需启用定时提醒任务：

```bash
celery -A app.tasks.celery_app beat --loglevel=info
```

### 4. 启动 Web 管理端

```bash
cd web-admin
npm install
npm run dev
```

访问：http://localhost:5173

### 5. 启动微信小程序

```bash
cd miniprogram
npm install
npm run dev:mp-weixin
```

然后用微信开发者工具导入 `miniprogram/dist/dev/mp-weixin`。本地联调时在开发者工具中勾选“不校验合法域名”，生产发布时需在微信公众平台配置 HTTPS 合法域名。

## 演示账号

| 角色 | 手机号 | 密码 |
| --- | --- | --- |
| 管理员 | `13800000001` | `admin123` |
| 医生 | `13800000002` | `doctor123` |
| 老人 | `13800000003` | `elder123` |

## AI 推理策略

后端通过环境变量控制推理策略：

```env
AI_MODEL_STRATEGY=hybrid
DEEP_MODEL_CHECKPOINT=models/deep_multimodal_fusion.pt
DEEP_MODEL_DEVICE=cpu
DEEP_MODEL_ALLOW_RANDOM_INIT=false
DEEP_MODEL_BLEND_ALPHA=0.65
```

取值说明：

| 策略 | 说明 |
| --- | --- |
| `rule` | 只使用规则模型，适合最稳演示 |
| `deep` | 只使用深度模型，要求 checkpoint 可用 |
| `hybrid` | 规则 + 深度融合，当前推荐 |

当深度模型不可用时，系统会回退到规则模型，评估流程不会中断。

## 常见问题

**端口被占用**

修改 `.env` 中的 `NGINX_HTTP_PORT`、`BACKEND_PORT`、`MYSQL_PORT` 等端口后重新启动。

**后端连不上数据库**

先确认 MySQL 健康状态：

```bash
docker compose ps mysql
docker compose logs mysql
```

**Web 能打开但接口失败**

开发模式下 Web 请求 `/api/v1`，需要 Vite 或 Nginx 代理到后端；Docker 模式由 Nginx 统一代理，本地开发可直接访问后端 Swagger 排查接口。

**小程序请求失败**

开发者工具勾选“不校验合法域名”；生产环境在微信公众平台把 `https://api.yishouxinan.site` 或实际 API 域名加入 request 合法域名。

*文档修订：2026-04-29*
