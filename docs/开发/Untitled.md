# 文档修订记录

本文用于记录本轮文档梳理中统一修正的口径，避免后续文档再次出现“规划目录”和“当前代码目录”混用。

## 2026-04-29 修订要点

| 项目 | 修订口径 |
| --- | --- |
| 前端目录 | 使用 `web-admin/` 与 `miniprogram/`，不再写作 `frontend/web-admin`、`frontend/miniprogram` |
| AI 服务 | 当前无独立 `ai-engine/` 目录，深度多模态推理集成在 `backend/app/services/deep_model_service.py` |
| API 响应 | 以 FastAPI 原生响应为准，不写统一 `{code,message,data}` 包装 |
| API 路由 | 当前路由为 `/api/v1/auth`、`/users`、`/assessments`、`/questions`、`/communities`、`/dashboard`、`/interventions`、`/notifications`、`/rag` |
| 报告接口 | 医生 PDF、家庭可读报告、趋势接口位于 `/api/v1/assessments` 下 |
| 多模态上传 | 当前音频上传位于 `/api/v1/assessments/sessions/{session_id}/uploads/audio` |
| 部署入口 | 根目录 `docker-compose.yml` 是当前主要部署入口，`infrastructure/docker-compose.yml` 作为辅助参考 |
| 端口 | 默认端口以 `.env.example` 与根目录 `docker-compose.yml` 为准 |

## 后续维护建议

新增或修改接口后，优先同步：

1. `docs/接口/接口设计.md`
2. `docs/系统架构/系统架构设计.md`
3. `docs/部署/部署说明.md`
4. `README.md` 与 `QUICKSTART.md`

如果只调整竞赛表述或商业计划，不需要同步接口文档；如果调整真实代码目录、环境变量或启动命令，必须同步入口文档。
