import asyncio

from skiptlu.client.session import QuizAttempt
from skiptlu.handlers.simple import QuizHandler
from skiptlu.models.activity import Activity, CompletionRequirement, CompletionStatus, ModuleType


class FakeSession:
    def __init__(self, result):
        self.result = result
        self.submit_called = False
        self.started = QuizAttempt(
            activity_id=result.activity_id,
            attempt_id="new",
            started=True,
            submitted=False,
        )

    async def start_quiz_attempt(self, activity):
        return self.started

    async def submit_quiz_attempt(self, activity, attempt):
        self.submit_called = True
        return self.result


def test_quiz_handler_submits_attempt_but_does_not_claim_pass_without_grade():
    async def run():
        result = QuizAttempt(
            activity_id=1,
            attempt_id="1",
            started=True,
            submitted=True,
            grade=6,
            grade_to_pass=7,
            passed=False,
            ready_to_submit=True,
        )
        handler = QuizHandler(FakeSession(result))
        activity = Activity(
            id=1,
            module=ModuleType.QUIZ,
            name="Quiz",
            url="https://example.test/quiz",
            requirements=[
                CompletionRequirement(type="Receive a passing grade")
            ],
        )

        status = await handler.execute(activity)

        assert status == CompletionStatus.INCOMPLETE
        assert handler.last_attempt.attempt_id == "new"
        assert not handler.session.submit_called

    asyncio.run(run())
