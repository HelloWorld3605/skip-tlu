from typing import Protocol

from .models import FeedbackQuestion, FeedbackResponsePlan


class FeedbackResponseProvider(Protocol):
    async def build_plan(
        self,
        questions: tuple[FeedbackQuestion, ...],
    ) -> FeedbackResponsePlan: ...


class NoResponseProvider:
    """Safe default: never invent feedback responses."""

    async def build_plan(self, questions):
        return FeedbackResponsePlan()
