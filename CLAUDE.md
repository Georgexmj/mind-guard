# MindGuard

社区老年认知障碍早期筛查与干预系统。三端架构：FastAPI 后端 + React 管理端 + UniApp 微信小程序。

## 项目结构

```
backend/          — FastAPI 后端（Python 3.11）
web-admin/        — 管理端 Web 应用（React 18 + TypeScript）
miniprogram/      — 微信小程序老人端（UniApp + Vue 3）
infrastructure/   — 辅助 Docker Compose + MySQL 初始化脚本
nginx/            — 开发/生产 Nginx 配置与证书目录
data/             — 训练数据、题库种子数据
docs/             — 项目文档（架构、需求、部署、商业计划）
```

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端框架 | FastAPI 0.110 + Uvicorn |
| ORM | SQLAlchemy 2.0（declarative base） |
| 数据库 | MySQL 8.0（PyMySQL） |
| 缓存/队列 | Redis 7（Celery 5.3 异步任务） |
| 对象存储 | MinIO（音频/画图文件） |
| AI/ML | PyTorch 2.2 + scikit-learn + LightGBM |
| 管理端 | React 18 + TypeScript + Vite 5 + Ant Design 5 |
| 状态管理 | Zustand 4（persist 中间件，localStorage） |
| 图表 | ECharts 5（echarts-for-react） |
| 小程序 | UniApp 3（Vue 3 Composition API）+ Pinia |
| 小程序 UI | @dcloudio/uni-ui |

## 开发环境启动

### 1. 基础设施

```bash
docker compose up -d mysql redis minio influxdb mongodb
```

### 2. 后端

```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.initial_data   # 初始化数据库 + 种子数据
uvicorn app.main:app --reload --port 8000
```

### 3. Celery Worker（单独终端）

```bash
cd backend && source .venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2 -Q ai_analysis,celery
```

### 4. 管理端

```bash
cd web-admin && npm install && npm run dev
# 运行在 http://localhost:5173，自动代理 /api → localhost:8000
```

### 5. 小程序

用微信开发者工具打开 `miniprogram/` 目录，构建目标为 `mp-weixin`。

### 测试账号

| 角色 | 手机号 | 密码 |
|------|--------|------|
| 管理员 | 13800000001 | admin123 |
| 医生 | 13800000002 | doctor123 |
| 老人 | 13800000003 | elder123 |

## 常用命令

```bash
# 后端
uvicorn app.main:app --reload --port 8000        # 启动开发服务器
python -m app.initial_data                         # 重置种子数据
celery -A app.tasks.celery_app worker --loglevel=info  # 启动 Celery

# 管理端
cd web-admin && npm run dev                        # 开发服务器
cd web-admin && npm run build                      # 生产构建

# Docker 一键部署（生产）
docker compose up -d --build
```

## 代码规范

### 后端（Python）

- **三层架构**：Router（HTTP 边界 + 鉴权）→ Service（业务逻辑）→ SQLAlchemy ORM（数据访问）
- **命名**：全部 `snake_case`（文件名、函数、变量、数据库列）
- **路由定义**：`APIRouter(prefix="/api/v1/<resource>", tags=[...])`
- **依赖注入**：`db: Session = Depends(get_db)` + `current_user = Depends(get_current_user)` 或 `Depends(require_role(...))`
- **Schema 约定**：
  - 输出 Schema 使用 `model_config = ConfigDict(from_attributes=True)` 启用 ORM 模式
  - 更新 Schema 字段全部 `Optional`，配合 `model_dump(exclude_unset=True)` 实现 PATCH 更新
  - 输入校验用 `@field_validator` with `mode="before"`
- **枚举**：继承 `str, enum.Enum`，值为小写字符串
- **JSON 列**：`answer_data`、`domain_scores`、`shap_values` 等使用 `Column(JSON)` 存储可扩展数据
- **软删除**：Question 使用 `is_active=False` 而非物理删除
- **新增 model 后**：必须在 `main.py` 顶部 import 该 model 模块，确保 `create_all` 能注册表

### 管理端（TypeScript/React）

- **文件命名**：页面 `PascalCasePage.tsx`，组件 `PascalCase.tsx`
- **类型定义**：集中在 `src/types/index.ts`
- **API 层**：`src/services/api.ts` 中导出命名函数（非 class），Axios 实例统一处理 token 注入和 401 跳转
- **状态管理**：Zustand store + persist 中间件，token 存 `localStorage`
- **严格模式**：TypeScript `strict: true`

### 小程序（Vue 3 / JavaScript）

- **语言**：纯 JavaScript（无 TypeScript）
- **组件模式**：`<script setup>` Composition API
- **样式单位**：`rpx`（微信响应式像素）
- **适老化设计**：基础字号 `36rpx`，按钮最小高度 `88rpx`，大触摸区域
- **主色调**：`#4A90D9`（蓝色）
- **风险色彩**：绿色 `#52C41A`（正常）、橙色 `#FA8C16`（轻度风险）、红色 `#F5222D`（高风险）
- **角色锁定**：小程序仅允许 `elder` 角色登录
- **存储**：使用 `wx.getStorageSync`/`wx.setStorageSync`（非 localStorage）

## API 约定

- 所有接口路径前缀：`/api/v1/`
- 认证：JWT Bearer token（`Authorization: Bearer <token>`）
- Access token 60 分钟过期，Refresh token 7 天
- JWT payload：`{ sub: user_id, role: role, type: "access"|"refresh" }`
- 角色守卫：`require_role("admin", "doctor")` 等，返回 403
- 四种角色：`elder`、`family`、`doctor`、`admin`

## AI 模型策略

通过环境变量 `AI_MODEL_STRATEGY` 切换（无需改代码）：

| 策略 | 说明 |
|------|------|
| `rule` | 纯规则引擎评分 |
| `deep` | PyTorch 深度多模态融合模型（不可用时回退到 rule） |
| `hybrid`（默认） | 规则 + 深度模型加权融合，权重由 `DEEP_MODEL_BLEND_ALPHA`（默认 0.65）控制 |

六个认知域：`memory`、`orientation`、`language`、`attention`、`visuospatial`、`executive`

三个风险等级：`normal`、`mild_risk`、`high_risk`

评估完成后通过 Celery 异步任务分析，客户端轮询 task 状态获取结果。

## 数据库

- 使用 `Base.metadata.create_all()` 在启动时自动建表
- Alembic 已安装但未启用迁移脚本
- 所有表使用 Integer 自增主键，`created_at` + `updated_at` 时间戳
- 连接池：`pool_size=10`，`max_overflow=20`，`pool_recycle=3600`

## 部署

Docker Compose 配置：

| 文件 | 用途 | 特点 |
|------|------|------|
| `/docker-compose.yml` | 当前主要入口 | 读 `.env` 文件，包含 MySQL、Redis、MinIO、InfluxDB、MongoDB、backend、Celery、web_admin、nginx |
| `/infrastructure/docker-compose.yml` | 辅助参考 | 基础设施与初始化脚本参考，实际部署优先使用根目录 compose |

默认端口以 `.env.example` 为准：Web/Nginx 30000、API 8000、MySQL 3306、Redis 6379、MinIO 9000/9001、InfluxDB 8086、MongoDB 27017。生产环境可在 `.env` 中改为 80/443 等正式端口。

## 注意事项

- 当前无测试套件（竞赛原型阶段）
- 无 linter/formatter 配置（无 ESLint、Ruff、Black）
- 无 pre-commit hooks
- Docker 构建使用国内镜像源（阿里云 apt、清华 PyPI、淘宝 npm）
- 深度模型权重文件 `backend/models/deep_multimodal_fusion.pt` 已提交到仓库
