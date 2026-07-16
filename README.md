# 包包刺绣 DIY 商城

本仓库是包包刺绣 DIY 商城的 monorepo。当前为第 1 阶段工程骨架，仅包含开发环境、健康检查和页面占位，不包含业务、平台登录或支付。

## 目录

- `apps/miniapp`：uni-app 用户端
- `apps/admin-web`：Vue 3 管理后台
- `services/api`：FastAPI 后端
- `infra`：基础设施说明
- `docs`：项目文档

## Docker Compose 启动

1. 复制环境变量：`Copy-Item .env.example .env`
2. 启动：`docker compose up --build`
3. 后端健康检查：<http://localhost:8000/api/health>
4. 管理后台：<http://localhost:5173>
5. 用户端 H5：<http://localhost:5174>

## 本地启动

用户端：

```powershell
cd apps/miniapp
npm install
npm run dev:h5
```

管理后台：

```powershell
cd apps/admin-web
npm install
npm run dev
```

后端（Python 3.11）：

```powershell
cd services/api
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

## 测试

```powershell
cd services/api
pytest
```

前端执行：

```powershell
npm run type-check
npm run build
```
