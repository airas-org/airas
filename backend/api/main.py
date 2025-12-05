from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes.v1 import (
    bibfile,
    code,
    experimental_settings,
    hypotheses,
    papers,
    repositories,
)
from src.airas.core.container import Container


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.container = Container()
    app.state.container.wire(packages=["api.routes.v1"])
    await app.state.container.init_resources()

    try:
        yield
    finally:
        await app.state.container.shutdown_resources()
        app.state.container.unwire()


app = FastAPI(title="AIRAS API", version="0.0.1", lifespan=lifespan)
app.include_router(papers.router, prefix="/airas/v1")
app.include_router(hypotheses.router, prefix="/airas/v1")
app.include_router(experimental_settings.router, prefix="/airas/v1")
app.include_router(code.router, prefix="/airas/v1")
app.include_router(repositories.router, prefix="/airas/v1")
app.include_router(bibfile.router, prefix="/airas/v1")
