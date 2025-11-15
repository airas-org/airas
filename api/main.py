from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes.v1 import create, papers
from src.airas.core.container import Container


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.container = Container()
    app.state.container.wire(packages=["api.routes.v1"])
    await app.state.container.init_resources()

    try:
        yield
    finally:
        await app.state.container.close()
        app.state.container.unwire()


app = FastAPI(title="AIRAS API", version="0.0.1", lifespan=lifespan)
app.include_router(papers.router, prefix="/airas/v1")
app.include_router(create.router, prefix="/airas/v1")
