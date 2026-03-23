from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from uuid import UUID

from airas.infra.db.models.feedback import FeedbackCategory, FeedbackModel
from airas.repository.feedback_repository import FeedbackRepository

logger = logging.getLogger(__name__)


# Abstract notifier interface. Subclass this for each delivery channel
# (e.g. EmailFeedbackNotifier, SlackFeedbackNotifier) and inject
# the concrete instances into FeedbackService via the `notifiers` parameter.
class FeedbackNotifier(ABC):
    @abstractmethod
    def notify(self, feedback: FeedbackModel) -> None: ...


class FeedbackService:
    def __init__(
        self,
        repo: FeedbackRepository,
        notifiers: list[FeedbackNotifier] | None = None,
    ):
        self.repo = repo
        self.notifiers = list(notifiers) if notifiers else []

    def create(
        self,
        *,
        created_by: UUID,
        category: FeedbackCategory,
        subject: str,
        detail: str,
        email: str | None = None,
    ) -> FeedbackModel:
        feedback = FeedbackModel(
            category=category,
            subject=subject,
            detail=detail,
            email=email,
            created_by=created_by,
        )
        saved = self.repo.create(feedback)
        self._run_notifiers(saved)
        return saved

    def list_by_user(
        self,
        created_by: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FeedbackModel]:
        return self.repo.list_by_user(created_by, limit=limit, offset=offset)

    def _run_notifiers(self, feedback: FeedbackModel) -> None:
        for notifier in self.notifiers:
            try:
                notifier.notify(feedback)
            except Exception:
                logger.exception(
                    "feedback notifier failed",
                    extra={
                        "feedback_id": str(feedback.id),
                        "notifier": notifier.__class__.__name__,
                    },
                )
