import os
from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import AsyncContextManager

from dependency_injector import providers
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

import api.routes.v1 as routes_v1
from airas.container import Container
from airas.infra.db.models.verification import (
    VerificationModel as _VerificationModel,  # noqa: F401
)
from airas.usecases.autonomous_research.in_memory_e2e_research_service import (
    InMemoryE2EResearchService,
)
from api.ee.auth.dependencies import get_current_user_id
from api.ee.settings import get_ee_settings
from api.routes.v1 import (
    bibfile,
    code,
    datasets,
    experimental_settings,
    experiments,
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


def _make_lifespan(
    enable_enterprise: bool,
) -> Callable[[FastAPI], AsyncContextManager[None]]:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        database_url = os.getenv("DATABASE_URL")
        # Railway provides postgresql:// but SQLAlchemy needs the psycopg driver specified
        if database_url and database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://", "postgresql+psycopg://", 1
            )
        container = Container()
        container.config.from_dict({"database_url": database_url})

        # Make container discoverable by dependency_injector's FastAPI integration
        app.state.container = container
        app.container = container

        if database_url:
            engine = container.engine()
            SQLModel.metadata.create_all(engine)
        else:
            container.e2e_research_service.override(
                providers.Singleton(InMemoryE2EResearchService)
            )

        # Wire only the packages whose routes are actually registered.
        packages: list = [routes_v1]
        if enable_enterprise:
            import api.ee as ee_pkg

            packages.append(ee_pkg)
        container.wire(packages=packages)
        await container.init_resources()

        try:
            yield
        finally:
            await container.shutdown_resources()
            container.unwire()

    return lifespan


def register_ee_routes(application: FastAPI) -> None:
    """Register all Enterprise Edition routes."""
    from api.ee.api_keys.routes import router as ee_api_keys_router
    from api.ee.auth.routes import router as ee_auth_router
    from api.ee.github_oauth.routes import router as ee_github_oauth_router
    from api.ee.plan.routes import router as ee_plan_router
    from api.ee.stripe.routes import router as ee_stripe_router

    application.include_router(ee_auth_router, prefix="/airas/ee")
    application.include_router(ee_api_keys_router, prefix="/airas/ee")
    application.include_router(ee_plan_router, prefix="/airas/ee")
    application.include_router(ee_stripe_router, prefix="/airas/ee")
    application.include_router(ee_github_oauth_router, prefix="/airas/ee")


def create_app(*, enable_enterprise: bool) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        enable_enterprise: Control EE route registration explicitly.
    """
    application = FastAPI(
        title="AIRAS API",
        version="0.0.1",
        lifespan=_make_lifespan(enable_enterprise),
    )

    @application.get("/health")
    def health():
        return {"status": "ok"}

    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://app.airas.io",
            "https://app-dev.airas.io",
        ],
        allow_origin_regex=r"https://(airas.*\.vercel\.app|.*\.trycloudflare\.com)|http://(localhost|127\.0\.0\.1):\d+",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    auth_deps = [Depends(get_current_user_id)]
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
    ]
    for router in v1_routers:
        application.include_router(router, prefix="/airas/v1", dependencies=auth_deps)

    if enable_enterprise:
        register_ee_routes(application)

    return application


# Module-level instance used by uvicorn (api.main:app) and runtime.
app = create_app(enable_enterprise=get_ee_settings().enabled)
