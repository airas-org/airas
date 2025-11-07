# api/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI

# from api.dependencies.container import Container
from api.routes.v1 import papers

# from api.errors import setup_exception_handlers
# from api.middlewares import setup_middlewares


@asynccontextmanager
async def lifespan(app: FastAPI):
    # app.state.container = Container()        # 生成：DB/HTTPクライアント/セッションファクトリ等
    try:
        yield
    finally:
        await app.state.container.close()  # 破棄：接続やクライアントを確実にクローズ


app = FastAPI(title="AIRAS API", version="0.0.1", lifespan=lifespan)
# setup_middlewares(app)
# setup_exception_handlers(app)
# app.include_router(experiments.router, prefix="/airas/v1")
app.include_router(papers.router, prefix="/airas/v1")
