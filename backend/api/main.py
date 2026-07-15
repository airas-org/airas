from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import api.routes.v1 as routes_v1
from airas.container import Container
from api.routes.v1 import (
    bibfile,
    code,
    datasets,
    experimental_settings,
    experiments,
    feedback,
    github,
    github_actions,
    hypotheses,
    hypothesis_driven_research,
    interactive_repo_agent,
    latex,
    models,
    papers,
    repositories,
    research_history,
    topic_open_ended_research,
    verification,
)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    container = Container()

    # Make container discoverable by dependency_injector's FastAPI integration
    app.state.container = container
    app.container = container

    container.wire(packages=[routes_v1])
    await container.init_resources()

    try:
        yield
    finally:
        await container.shutdown_resources()
        container.unwire()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="AIRAS API",
        version="0.0.1",
        lifespan=_lifespan,
    )

    @application.get("/health")
    def health():
        return {"status": "ok"}

    application.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    v1_routers = [
        papers.router,
        models.router,
        datasets.router,
        hypotheses.router,
        experimental_settings.router,
        experiments.router,
        code.router,
        repositories.router,
        bibfile.router,
        latex.router,
        research_history.router,
        github_actions.router,
        github.router,
        interactive_repo_agent.router,
        topic_open_ended_research.router,
        hypothesis_driven_research.router,
        verification.router,
        feedback.router,
    ]
    for router in v1_routers:
        application.include_router(router, prefix="/airas/v1")

    return application


# Module-level instance used by uvicorn (api.main:app) and runtime.
app = create_app()
