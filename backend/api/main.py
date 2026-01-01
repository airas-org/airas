import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

import api.routes.v1 as routes_v1
from airas.core.container import Container
from api.routes.v1 import (
    bibfile,
    code,
    datasets,
    e2e,
    experimental_settings,
    experiments,
    github_actions,
    hypotheses,
    latex,
    models,
    papers,
    repositories,
    research_history,
    session_steps,
    sessions,
    step_run_links,
)

DATABASE_URL = os.getenv("DATABASE_URL")


@asynccontextmanager
async def lifespan(app: FastAPI):
    container = Container()
    container.config.from_dict({"database_url": DATABASE_URL})

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

# Allow frontend (e.g., Vite dev server) to call the API with browser preflight
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
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
app.include_router(session_steps.router, prefix="/airas/v1")
app.include_router(step_run_links.router, prefix="/airas/v1")
app.include_router(e2e.router, prefix="/airas/v1")
