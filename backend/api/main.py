import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import SQLModel

import api.routes.v1 as routes_v1
from airas.core.container import Container
from api.routes.v1 import (
    bibfile,
    code,
    datasets,
    experimental_settings,
    experiments,
    github_actions,
    hypotheses,
    latex,
    models,
    papers,
    repositories,
    research_history,
    sessions,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    container = Container()
    container.config.from_dict({"database_url": os.getenv("DATABASE_URL")})

    # Make container discoverable by dependency_injector's FastAPI integration (request.app.container)
    app.state.container = container
    app.container = container

    engine = container.engine()
    SQLModel.metadata.create_all(engine)

    # Explicitly wire route modules so dependency_injector resolves Provide[] dependencies.
    container.wire(packages=[routes_v1])
    await container.init_resources()

    try:
        yield
    finally:
        await container.shutdown_resources()
        container.unwire()


app = FastAPI(title="AIRAS API", version="0.0.1", lifespan=lifespan)
app.include_router(papers.router, prefix="/airas/v1")
app.include_router(models.router, prefix="/airas/v1")
app.include_router(datasets.router, prefix="/airas/v1")
app.include_router(hypotheses.router, prefix="/airas/v1")
app.include_router(experimental_settings.router, prefix="/airas/v1")
app.include_router(experiments.router, prefix="/airas/v1")
app.include_router(code.router, prefix="/airas/v1")
app.include_router(repositories.router, prefix="/airas/v1")
app.include_router(bibfile.router, prefix="/airas/v1")
app.include_router(latex.router, prefix="/airas/v1")
app.include_router(research_history.router, prefix="/airas/v1")
app.include_router(github_actions.router, prefix="/airas/v1")
app.include_router(sessions.router, prefix="/airas/v1")
