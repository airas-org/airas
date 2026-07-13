from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from uuid import UUID

from airas.core.types.feedback import FeedbackCategory, FeedbackModel

logger = logging.getLogger(__name__)


# Abstract notifier interface. Subclass this for each delivery channel
# (e.g. EmailFeedbackNotifier, SlackFeedbackNotifier) and inject
# the concrete instances into FeedbackService via the `notifiers` parameter.
class FeedbackNotifier(ABC):
    @abstractmethod
    def notify(self, feedback: FeedbackModel) -> None: ...


class FeedbackService:
    """Deliver feedback via the configured notifiers (no persistence)."""

    def __init__(
        self,
        notifiers: list[FeedbackNotifier] | None = None,
    ):
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
        self._run_notifiers(feedback)
        return feedback

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
