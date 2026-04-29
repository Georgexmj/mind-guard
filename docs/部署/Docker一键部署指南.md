# Docker 一键部署指南（推荐）

本文档用于在项目根目录通过 `docker compose` 一键部署整套系统（MySQL、Redis、MinIO、InfluxDB、MongoDB、FastAPI、Celery、Web 管理端）。

## 1. 部署前准备

### 1.1 环境要求

- Docker Engine 24.0+
- Docker Compose 2.20+（Docker Desktop 内置）
- 建议内存 8GB 及以上（最低 4GB）
- 建议磁盘剩余 10GB 及以上

### 1.2 获取代码

```bash
git clone <你的仓库地址>
cd 基于多模态交互的社区老年认知障碍早期筛查与干预系统
```

## 2. 一键启动（首次部署）

### 2.1 准备环境变量

在项目根目录执行：

```bash
# Linux / macOS
cp .env.example .env

# Windows PowerShell
Copy-Item .env.example .env
```

如需改端口、密码、密钥，直接编辑根目录 `.env` 文件即可。

### 2.2 启动全部服务

```bash
docker compose up -d --build
```

首次构建会下载镜像并安装依赖，通常需要几分钟。

### 2.3 检查运行状态

```bash
docker compose ps
docker compose logs -f backend
```

当 `backend` 日志出现 `Application startup complete`（或 Uvicorn 启动日志）后，系统可用。

## 3. 访问地址与默认账号

### 3.1 访问地址

- Web 管理端：`http://localhost:30000`（由 `NGINX_HTTP_PORT` 控制）
- 后端 Swagger：`http://localhost:8000/docs`（由 `BACKEND_PORT` 控制）
- MinIO 控制台：`http://localhost:9001`（由 `MINIO_CONSOLE_PORT` 控制）
- InfluxDB：`http://localhost:8086`（由 `INFLUXDB_PORT` 控制）

### 3.2 演示账号（由种子数据自动创建）

- 管理员：`13800000001 / admin123`
- 医生：`13800000002 / doctor123`
- 老人：`13800000003 / elder123`

## 4. 常用运维命令

### 4.1 查看日志

```bash
docker compose logs -f
docker compose logs -f backend
docker compose logs -f celery_worker
```

### 4.2 停止服务

```bash
docker compose down
```

### 4.3 重启某个服务

```bash
docker compose restart backend
docker compose restart web_admin
```

### 4.4 完全重置数据（危险操作）

```bash
docker compose down -v
docker compose up -d --build
```

说明：`-v` 会删除 MySQL/Redis/MinIO/MongoDB/InfluxDB 的持久化数据卷。

## 5. 端口与配置说明

可在根目录 `.env` 中覆盖以下常用变量：

- `NGINX_HTTP_PORT`（默认 `30000`）
- `NGINX_HTTPS_PORT`（默认 `30443`）
- `BACKEND_PORT`（默认 `8000`）
- `MYSQL_PORT`（默认 `3306`）
- `REDIS_PORT`（默认 `6379`）
- `MINIO_API_PORT`（默认 `9000`）
- `MINIO_CONSOLE_PORT`（默认 `9001`）
- `INFLUXDB_PORT`（默认 `8086`）
- `MONGODB_PORT`（默认 `27017`）

如果遇到端口占用，把左侧端口改为未占用端口即可（例如 `NGINX_HTTP_PORT=30010`）。

## 6. 常见问题排查

### 6.1 `port is already allocated`

有其他程序占用了端口。修改 `.env` 中对应端口并重启：

```bash
docker compose down
docker compose up -d
```

### 6.2 后端启动失败，提示数据库连接失败

先确认 MySQL 健康状态：

```bash
docker compose ps
docker compose logs -f mysql
```

等待 MySQL 完全 ready 后，重启后端：

```bash
docker compose restart backend
```

### 6.3 Web 页面能打开但接口报错

排查顺序：

1. `docker compose ps` 看 `backend` 是否 `running/healthy`
2. 打开 `http://localhost:8000/health` 检查后端健康状态
3. 查看 `backend` 与 `web_admin` 日志是否有 502/连接错误

## 7. 生产部署建议

- 必须修改 `.env` 中所有默认密码与 `SECRET_KEY`
- 建议只暴露 Nginx 80/443，后端、数据库和对象存储仅允许内网访问
- 定期备份 MySQL 与 MinIO 数据卷
- 资源紧张时可先关闭非核心组件（InfluxDB/MongoDB）

## 8. 说明

- 当前根目录 `docker-compose.yml` 已包含完整编排，建议统一使用该文件。
- 为避免与当前后端 ORM 模型冲突，本一键部署流程不依赖 `infrastructure/mysql/init.sql`。
- 后端容器启动时会执行 `python -m app.initial_data`，自动建表并初始化演示数据。

## 9. Nginx 配置说明
当前项目提供多套 Nginx 配置文件：

- 开发环境：`nginx/nginx.dev.conf`
- 生产环境：`nginx/nginx.prod.conf`
- 当前 Compose 挂载入口：`nginx/nginx.conf`

根目录 `docker-compose.yml` 当前直接挂载 `./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro`，因此切换开发/生产配置时需要修改 compose 挂载项，或将目标配置内容同步到 `nginx/nginx.conf` 后重建 nginx。

## 10. 生产环境执行示例
在生产服务器上，建议在项目根目录 `.env` 中至少设置：

```env
NGINX_CONF_FILE=nginx.prod.conf
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443
```

然后确认 compose 挂载的证书目录与 `nginx/nginx.conf` 中的证书路径一致。当前仓库已有按域名拆分的证书目录，例如：

```text
nginx/admin.yishouxinan.site_nginx/
nginx/api.yishouxinan.site_nginx/
```

最后在项目根目录执行：

```bash
docker compose up -d --build
docker compose ps
```

如果只是从开发配置切换到生产配置，可执行：

```bash
docker compose up -d --force-recreate nginx
```
