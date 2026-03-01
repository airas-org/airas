import os
from contextlib import asynccontextmanager

from dependency_injector import providers
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

import api.routes.v1 as routes_v1
from airas.container import Container
from airas.usecases.autonomous_research.in_memory_e2e_research_service import (
    InMemoryE2EResearchService,
)
from api.ee.auth.dependencies import get_current_user_id
from api.ee.settings import get_ee_settings
from api.routes.v1 import (
    assisted_research,
    bibfile,
    code,
    datasets,
    experimental_settings,
    experiments,
    github,
    github_actions,
    hypotheses,
    hypothesis_driven_research,
    latex,
    models,
    papers,
    repositories,
    research_history,
    topic_open_ended_research,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    database_url = os.getenv("DATABASE_URL")
    # Railway provides postgresql:// but SQLAlchemy needs the psycopg driver specified
    if database_url and database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    container = Container()
    container.config.from_dict({"database_url": database_url})

    # Make container discoverable by dependency_injector's FastAPI integration (request.app.container)
    app.state.container = container
    app.container = container

    if database_url:
        engine = container.engine()
        SQLModel.metadata.create_all(engine)
    else:
        container.e2e_research_service.override(
            providers.Singleton(InMemoryE2EResearchService)
        )

    # Explicitly wire route modules so dependency_injector resolves Provide[] dependencies.
    import api.ee as ee_pkg

    container.wire(packages=[routes_v1, ee_pkg])
    await container.init_resources()

    try:
        yield
    finally:
        await container.shutdown_resources()
        container.unwire()


app = FastAPI(title="AIRAS API", version="0.0.1", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


# Allow frontend to call the API with browser preflight
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.airas.io",
        "https://app-dev.airas.io",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"https://airas.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
auth_deps = [Depends(get_current_user_id)]
app.include_router(papers.router, prefix="/airas/v1", dependencies=auth_deps)
app.include_router(models.router, prefix="/airas/v1", dependencies=auth_deps)
app.include_router(datasets.router, prefix="/airas/v1", dependencies=auth_deps)
app.include_router(hypotheses.router, prefix="/airas/v1", dependencies=auth_deps)
app.include_router(
    experimental_settings.router, prefix="/airas/v1", dependencies=auth_deps
)
app.include_router(experiments.router, prefix="/airas/v1", dependencies=auth_deps)
app.include_router(code.router, prefix="/airas/v1", dependencies=auth_deps)
app.include_router(repositories.router, prefix="/airas/v1", dependencies=auth_deps)
app.include_router(bibfile.router, prefix="/airas/v1", dependencies=auth_deps)
app.include_router(latex.router, prefix="/airas/v1", dependencies=auth_deps)
app.include_router(research_history.router, prefix="/airas/v1", dependencies=auth_deps)
app.include_router(github_actions.router, prefix="/airas/v1", dependencies=auth_deps)
app.include_router(github.router, prefix="/airas/v1", dependencies=auth_deps)
app.include_router(assisted_research.router, prefix="/airas/v1", dependencies=auth_deps)
app.include_router(
    topic_open_ended_research.router, prefix="/airas/v1", dependencies=auth_deps
)
app.include_router(
    hypothesis_driven_research.router, prefix="/airas/v1", dependencies=auth_deps
)

# Register EE routes if enterprise is enabled
_ee_settings = get_ee_settings()
if _ee_settings.enabled:
    from api.ee.api_keys.routes import router as ee_api_keys_router
    from api.ee.auth.routes import router as ee_auth_router
    from api.ee.plan.routes import router as ee_plan_router
    from api.ee.stripe.routes import router as ee_stripe_router

    app.include_router(ee_auth_router, prefix="/airas/ee")
    app.include_router(ee_api_keys_router, prefix="/airas/ee")
    app.include_router(ee_plan_router, prefix="/airas/ee")
    app.include_router(ee_stripe_router, prefix="/airas/ee")
