from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from skiptlu.models.activity import Activity, CompletionStatus, ModuleType
from skiptlu.client.session import QuizAttempt


@dataclass(frozen=True)
class VerificationResult:
    status: CompletionStatus
    evidence: dict[str, Any] = field(default_factory=dict)


class VerificationEngine:
    """Read authoritative Moodle state independently from activity handlers."""

    def __init__(self, session=None):
        self.session = session

    async def verify(self, activity: Activity) -> VerificationResult:
        if self.session is None:
            return VerificationResult(
                status=CompletionStatus.UNKNOWN,
                evidence={"reason": "Moodle session adapter is not connected."},
            )

        if activity.module == ModuleType.ASSIGNMENT:
            return await self._verify_assignment(activity)

        if activity.module == ModuleType.QUIZ:
            return await self._verify_quiz(activity)

        status = await self.session.read_completion(activity)
        return VerificationResult(
            status=status,
            evidence={
                "source": "moodle_completion_marker",
                "activity_id": activity.id,
            },
        )

    async def _verify_assignment(self, activity: Activity) -> VerificationResult:
        result = await self.session.read_assignment_submission(activity)
        return VerificationResult(
            status=result.completion,
            evidence={
                "source": "moodle_assignment_submission",
                "activity_id": result.activity_id,
                "has_submission": result.has_submission,
                "files": list(result.files),
                "status_text": result.status_text,
            },
        )

    async def _verify_quiz(self, activity: Activity) -> VerificationResult:
        result: QuizAttempt = await self.session.read_quiz_result(activity)
        needs_passing = any(
            "pass" in item.type.lower()
            or "passing" in item.type.lower()
            or str(item.metadata.get("condition", "")).lower() == "pass"
            for item in activity.requirements
        )

        if result.passed:
            status = CompletionStatus.PASSED
        elif result.submitted and not needs_passing:
            status = CompletionStatus.COMPLETE
        else:
            status = CompletionStatus.INCOMPLETE

        return VerificationResult(
            status=status,
            evidence={
                "source": "moodle_quiz_result",
                "activity_id": result.activity_id,
                "attempt_id": result.attempt_id,
                "submitted": result.submitted,
                "grade": result.grade,
                "grade_to_pass": result.grade_to_pass,
                "passed": result.passed,
                "status_text": result.status_text,
            },
        )
