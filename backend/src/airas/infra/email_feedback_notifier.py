from __future__ import annotations

import logging

import boto3

from airas.infra.db.models.feedback import FeedbackModel
from airas.usecases.feedback.feedback_service import FeedbackNotifier

logger = logging.getLogger(__name__)


class EmailFeedbackNotifier(FeedbackNotifier):
    """Send feedback notifications via Amazon SES."""

    def __init__(
        self,
        *,
        from_address: str,
        to_address: str,
        region_name: str = "ap-northeast-1",
    ):
        self.from_address = from_address
        self.to_address = to_address
        self.client = boto3.client("ses", region_name=region_name)

    def notify(self, feedback: FeedbackModel) -> None:
        reply_to = [feedback.email] if feedback.email else []
        subject = f"[AIRAS Feedback] [{feedback.category}] {feedback.subject}"
        body = (
            f"Category: {feedback.category}\n"
            f"Subject: {feedback.subject}\n"
            f"Email: {feedback.email or 'N/A'}\n"
            f"Feedback ID: {feedback.id}\n"
            f"Created at: {feedback.created_at}\n"
            f"\n---\n\n"
            f"{feedback.detail}"
        )

        try:
            self.client.send_email(
                Source=self.from_address,
                Destination={"ToAddresses": [self.to_address]},
                ReplyToAddresses=reply_to,
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {"Text": {"Data": body, "Charset": "UTF-8"}},
                },
            )
            logger.info(
                "Feedback email sent via Amazon SES",
                extra={
                    "feedback_id": str(feedback.id),
                    "to": self.to_address,
                },
            )
        except Exception:
            logger.exception(
                "Failed to send feedback email via Amazon SES",
                extra={
                    "feedback_id": str(feedback.id),
                    "to": self.to_address,
                },
            )
            raise
