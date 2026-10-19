import asyncio

from skiptlu.quiz.answering import NoAnswerProvider
from skiptlu.quiz.models import QuizQuestion


def test_no_answer_provider_never_invents_answers():
    async def run():
        questions = (
            QuizQuestion("1", 1, "Question", question_type="single_choice"),
        )
        plan = await NoAnswerProvider().build_plan(questions)
        assert plan.answers == ()
        assert not plan.is_complete_for(questions)

    asyncio.run(run())
