# CogniCare — 快速启动指南

本文档说明如何在本地快速跑通完整系统（后端 + Web管理端 + 数据库基础设施）。

---

## 环境要求

| 工具 | 版本要求 | 说明 |
|------|----------|------|
| Docker Desktop | 24.0+ | 运行所有基础设施 |
| Python | 3.11+ | 后端开发模式 |
| Node.js | 20+ | Web Admin 开发模式 |
| 微信开发者工具 | 最新版 | 小程序调试 |

---

## 方式一：Docker 一键启动（推荐演示使用）

```bash
# 1. 进入 infrastructure 目录
cd infrastructure

# 2. 启动所有服务（首次启动会构建镜像，约3~5分钟）
docker compose up -d

# 3. 查看所有服务状态
docker compose ps

# 4. 查看后端日志（等待 "Application startup complete" 字样）
docker compose logs -f backend
```

启动完成后访问：
- **Web 管理端**：http://localhost （admin/doctor 账号）
- **后端 API 文档**：http://localhost:8000/docs （Swagger UI）
- **MinIO 控制台**：http://localhost:9001 （cognitive_admin / cognitive_minio_2026）

停止所有服务：
```bash
docker compose down
```

清除数据重新初始化：
```bash
docker compose down -v   # 加 -v 会删除所有数据卷
docker compose up -d
```

---

## 方式二：本地开发模式（推荐开发调试）

### 步骤 1：启动基础设施（只启动数据库等，不含应用）

```bash
cd infrastructure
docker compose up -d mysql redis minio influxdb mongodb
```

等待约 20 秒让 MySQL 完全初始化。

### 步骤 2：启动后端

```bash
cd backend

# 安装依赖（建议用虚拟环境）
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate

pip install -r requirements.txt

# 初始化数据库并插入测试数据
python -m app.initial_data

# 启动 FastAPI（热重载）
uvicorn app.main:app --reload --port 8000
```

后端启动后：http://localhost:8000/docs

### 步骤 3：启动 Celery Worker（AI 异步分析）

新开一个终端：
```bash
cd backend
# 激活同一个虚拟环境
source .venv/bin/activate  # 或 Windows: .venv\Scripts\activate

celery -A app.tasks.celery_app worker --loglevel=info
```

### 步骤 4：启动 Web Admin

```bash
cd web-admin
npm install
npm run dev
```

访问：http://localhost:5173

### 步骤 5：启动小程序（微信开发者工具）

1. 打开微信开发者工具
2. 导入项目 → 选择 `miniprogram/` 目录
3. AppID 填写你的微信小程序 AppID（或使用"测试号"）
4. 在 `miniprogram/utils/request.js` 中将 BASE_URL 改为：
   ```javascript
   const BASE_URL = 'http://localhost:8000/api/v1'
   ```
5. 点击编译，即可在模拟器中运行

---

## 演示账号

| 角色 | 手机号 | 密码 | 说明 |
|------|--------|------|------|
| 管理员 | 13800000001 | admin123 | 完整权限，可管理所有数据 |
| 医生 | 13800000002 | doctor123 | 可查看老人评估结果 |
| 老人 | 13800000003 | elder123 | 小程序端登录，可完成评估 |

---

## 端口一览

| 服务 | 端口 | 说明 |
|------|------|------|
| Web Admin | 80 (Docker) / 5173 (Dev) | React 管理后台 |
| FastAPI | 8000 | REST API + Swagger |
| MySQL | 3306 | 主数据库 |
| Redis | 6379 | 缓存 + 消息队列 |
| MinIO API | 9000 | 文件存储 |
| MinIO Console | 9001 | 存储管理界面 |
| InfluxDB | 8086 | 时序数据库 |
| MongoDB | 27017 | 特征存储 |

---

## 完整评估流程演示

1. **小程序端（老人角色）**：
   - 用 13800000003 / elder123 登录
   - 点击"开始认知评估"
   - 完成 15 道题（包含选择题、语音题、时钟绘制）
   - 提交后等待 AI 分析（约 5~10 秒，Mock AI）
   - 查看评估报告（六维雷达图 + 风险评级）

2. **Web Admin（医生/管理员角色）**：
   - 用 13800000002 / doctor123 登录 http://localhost:5173
   - 仪表盘查看整体统计
   - 老人管理 → 查看老人列表
   - 评估管理 → 查看最新评估结果（包含认知雷达图）

---

## 常见问题

**Q: docker compose up 报错 "port already in use"**
```bash
# 检查占用端口的进程（以3306为例）
netstat -ano | findstr 3306   # Windows
lsof -i :3306                 # Mac/Linux
# 停止冲突进程后重试
```

**Q: 后端报 "Can't connect to MySQL server"**
```bash
# 等待MySQL完全启动（约15~20秒），或手动检查
docker compose logs mysql | tail -20
# 看到 "ready for connections" 字样才算启动完成
```

**Q: 小程序报 "request:fail url not in domain list"**
- 微信开发者工具 → 详情 → 本地设置 → 勾选"不校验合法域名"
- 或将 `http://localhost:8000` 添加到小程序后台的 request 合法域名

**Q: Celery Worker 连不上 Redis**
```bash
# 确认Redis在运行
docker compose ps redis
# 或直接用本地Redis
redis-cli ping  # 应返回 PONG
```

---

*文档版本：v1.0 | 2026-03*
