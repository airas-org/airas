from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import airas.dashboard.api.routes.v1 as routes_v1
from airas.container import Container
from airas.dashboard.api.routes.v1 import (
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

    _mount_dashboard_static(application)

    return application


class _SpaStaticFiles(StaticFiles):
    """Static files with SPA fallback: unknown paths serve index.html."""

    async def get_response(self, path, scope):
        from starlette.exceptions import HTTPException

        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            # Unknown API paths should stay 404s; only SPA routes fall back.
            if exc.status_code == 404 and not path.startswith("airas/"):
                return await super().get_response("index.html", scope)
            raise


def _mount_dashboard_static(application: FastAPI) -> None:
    # Present only in wheels built by CI (frontend/dist is copied in);
    # absent in development checkouts, where the Vite dev server is used.
    static_dir = Path(__file__).resolve().parent.parent / "static"
    if (static_dir / "index.html").is_file():
        application.mount(
            "/", _SpaStaticFiles(directory=static_dir, html=True), name="dashboard"
        )


# Module-level instance used by uvicorn (api.main:app) and runtime.
app = create_app()
