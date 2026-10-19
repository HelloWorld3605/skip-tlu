import asyncio

from skiptlu.feedback.answering import NoResponseProvider
from skiptlu.feedback.models import FeedbackQuestion, FeedbackQuestionType, FeedbackResponsePlan
from skiptlu.handlers.simple import FeedbackHandler
from skiptlu.models.activity import Activity, CompletionStatus, ModuleType


class FakeSession:
    async def read_feedback_questions(self, activity):
        return (
            FeedbackQuestion(
                question_id="q1",
                number=1,
                prompt="Comment",
                question_type=FeedbackQuestionType.TEXT,
                required=True,
            ),
        )

    async def fill_feedback_responses(self, activity, plan):
        return plan.responses != ()

    async def submit_feedback(self, activity):
        return CompletionStatus.COMPLETE

    async def read_completion(self, activity):
        return CompletionStatus.COMPLETE


class EmptyProvider:
    async def build_plan(self, questions):
        return FeedbackResponsePlan()


class ExplicitProvider:
    async def build_plan(self, questions):
        from skiptlu.feedback.models import FeedbackResponse
        return FeedbackResponsePlan(
            responses=(FeedbackResponse("q1", ("user supplied",)),)
        )


def test_feedback_handler_default_does_not_submit():
    async def run():
        handler = FeedbackHandler(FakeSession(), NoResponseProvider())
        activity = Activity(id=1, module=ModuleType.FEEDBACK, name="Feedback", url="https://example.test")
        assert await handler.execute(activity) == CompletionStatus.INCOMPLETE

    asyncio.run(run())


def test_feedback_handler_uses_explicit_response_plan():
    async def run():
        handler = FeedbackHandler(FakeSession(), ExplicitProvider())
        activity = Activity(id=1, module=ModuleType.FEEDBACK, name="Feedback", url="https://example.test")
        assert await handler.execute(activity) == CompletionStatus.COMPLETE

    asyncio.run(run())
