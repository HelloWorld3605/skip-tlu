import asyncio

from skiptlu.client.session import QuizAttempt
from skiptlu.completion.verification import VerificationEngine
from skiptlu.models.activity import Activity, CompletionRequirement, CompletionStatus, ModuleType


class FakeQuizSession:
    def __init__(self, result):
        self.result = result
        self.calls = []

    async def read_quiz_result(self, activity):
        self.calls.append(activity.id)
        return self.result


def test_quiz_verification_requires_passing_when_requirement_exists():
    async def run():
        session = FakeQuizSession(
            QuizAttempt(
                activity_id=51560,
                attempt_id="42",
                submitted=True,
                grade=6.0,
                grade_to_pass=7.0,
                passed=False,
            )
        )
        verifier = VerificationEngine(session)
        activity = Activity(
            id=51560,
            module=ModuleType.QUIZ,
            name="Weekly quiz",
            requirements=[
                CompletionRequirement(type="Receive a grade"),
                CompletionRequirement(type="Receive a passing grade"),
            ],
        )

        result = await verifier.verify(activity)

        assert result.status == CompletionStatus.INCOMPLETE
        assert result.evidence["grade"] == 6.0
        assert result.evidence["grade_to_pass"] == 7.0

    asyncio.run(run())


def test_quiz_verification_returns_passed():
    async def run():
        session = FakeQuizSession(
            QuizAttempt(
                activity_id=51560,
                attempt_id="43",
                submitted=True,
                grade=8.0,
                grade_to_pass=7.0,
                passed=True,
            )
        )
        verifier = VerificationEngine(session)
        activity = Activity(
            id=51560,
            module=ModuleType.QUIZ,
            name="Weekly quiz",
            requirements=[
                CompletionRequirement(type="Receive a passing grade"),
            ],
        )

        result = await verifier.verify(activity)

        assert result.status == CompletionStatus.PASSED
        assert result.evidence["passed"] is True

    asyncio.run(run())
