from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes.v1 import papers
from src.airas.services.api_client.api_clients_container import (
    AsyncContainer,
    SyncContainer,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.sync_container = SyncContainer()
    app.state.async_container = AsyncContainer()

    app.state.sync_container.wire(packages=["api.routes.v1"])
    app.state.async_container.wire(packages=["api.routes.v1"])

    # リソース初期化
    app.state.sync_container.init_resources()
    app.state.async_container.init_resources()

    try:
        yield
    finally:
        app.state.sync_container.close()  # 破棄：接続やクライアントを確実にクローズ
        await app.state.async_container.close()

        app.state.sync_container.unwire()
        app.state.async_container.unwire()


app = FastAPI(title="AIRAS API", version="0.0.1", lifespan=lifespan)
app.include_router(papers.router, prefix="/airas/v1")
