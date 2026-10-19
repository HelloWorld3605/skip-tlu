from __future__ import annotations

from typing import Protocol

from .models import QuizAnswerPlan, QuizQuestion


class QuizAnswerProvider(Protocol):
    async def build_plan(
        self,
        questions: tuple[QuizQuestion, ...],
    ) -> QuizAnswerPlan: ...


class NoAnswerProvider:
    """Safe default: never invent answers."""

    async def build_plan(self, questions):
        return QuizAnswerPlan()
