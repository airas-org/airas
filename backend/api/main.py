import os
from contextlib import asynccontextmanager

from dependency_injector import providers
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

import api.routes.v1 as routes_v1
from airas.container import Container
from airas.infra.db.models.feedback import (
    FeedbackModel as _FeedbackModel,  # noqa: F401
)
from airas.infra.db.models.verification import (
    VerificationModel as _VerificationModel,  # noqa: F401
)
from airas.usecases.autonomous_research.in_memory_e2e_research_service import (
    InMemoryE2EResearchService,
)
from api.ee.auth.dependencies import get_current_user_id
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
    database_url = os.getenv("DATABASE_URL")
    # Railway provides postgresql:// but SQLAlchemy needs the psycopg driver specified
    if database_url and database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
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

    _configure_feedback_email_notifier(container)

    import api.ee as ee_pkg

    container.wire(packages=[routes_v1, ee_pkg])
    await container.init_resources()

    try:
        yield
    finally:
        await container.shutdown_resources()
        container.unwire()


def _configure_feedback_email_notifier(container: Container) -> None:
    """Override feedback_service with email notifier if SMTP env vars are set."""
    smtp_host = os.getenv("FEEDBACK_SMTP_HOST")
    to_address = os.getenv("FEEDBACK_TO_EMAIL")
    if not smtp_host or not to_address:
        return

    from airas.infra.email_feedback_notifier import EmailFeedbackNotifier
    from airas.usecases.feedback.feedback_service import FeedbackService

    notifier = EmailFeedbackNotifier(
        smtp_host=smtp_host,
        smtp_port=int(os.getenv("FEEDBACK_SMTP_PORT", "587")),
        smtp_user=os.getenv("FEEDBACK_SMTP_USER", ""),
        smtp_password=os.getenv("FEEDBACK_SMTP_PASSWORD", ""),
        from_address=os.getenv("FEEDBACK_FROM_EMAIL", to_address),
        to_address=to_address,
        use_tls=os.getenv("FEEDBACK_SMTP_USE_TLS", "true").lower() == "true",
        use_ssl=os.getenv("FEEDBACK_SMTP_USE_SSL", "false").lower() == "true",
    )

    container.feedback_service.override(
        providers.Factory(
            FeedbackService,
            repo=container.feedback_repository,
            notifiers=[notifier],
        )
    )


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
        feedback.router,
    ]
    for router in v1_routers:
        application.include_router(router, prefix="/airas/v1", dependencies=auth_deps)

    register_ee_routes(application)

    return application


# Module-level instance used by uvicorn (api.main:app) and runtime.
app = create_app()
