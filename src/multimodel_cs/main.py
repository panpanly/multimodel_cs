"""
后端接口入口
"""
from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.multimodel_cs.api.routers import router
from src.multimodel_cs.config.logging_config import setup_logging
from src.multimodel_cs.config.setting import settings



setup_logging()

app = FastAPI(
    title="多模态智能客服",
    version="1.0",
    description="一个基于多模态的智能客服系统",
    docs_url="/docs"
)

# 配置中间键
app.add_middleware(
    CORSMiddleware,
    allow_origins= settings.ALLOW_ORIGINS,
    allow_credentials=True, # 允许携带cookie
    allow_methods=["*"], # 允许所有HTTP方法
    allow_headers=["*"], # 允许所有HTTP头
)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory=settings.STATIC_PATH),name="static")

# 包含API路由
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app,host="127.0.0.1", port=8000)
