import asyncio

from skiptlu.feedback.answering import NoResponseProvider
from skiptlu.feedback.models import FeedbackQuestion, FeedbackQuestionType


def test_no_response_provider_does_not_invent_feedback():
    async def run():
        questions = (
            FeedbackQuestion(
                question_id="1",
                number=1,
                prompt="Question",
                question_type=FeedbackQuestionType.TEXT,
                required=True,
            ),
        )
        plan = await NoResponseProvider().build_plan(questions)
        assert plan.responses == ()
        assert not plan.is_complete_for(questions)

    asyncio.run(run())
