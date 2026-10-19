from skiptlu.client.session import MoodleSession
from skiptlu.feedback.answering import FeedbackResponseProvider, NoResponseProvider
from skiptlu.feedback.models import FeedbackResponsePlan
from skiptlu.handlers.base import ActivityHandler
from skiptlu.models.activity import Activity, CompletionStatus


class FeedbackHandler(ActivityHandler):
    """Process Moodle feedback only with an explicit response provider."""

    def __init__(
        self,
        session: MoodleSession | None = None,
        response_provider: FeedbackResponseProvider | None = None,
    ):
        self.session = session
        self.response_provider = response_provider or NoResponseProvider()

    async def execute(self, activity: Activity) -> CompletionStatus:
        if self.session is None or not activity.url:
            return CompletionStatus.INCOMPLETE

        questions = await self.session.read_feedback_questions(activity)
        plan = await self.response_provider.build_plan(questions)

        if not plan.is_complete_for(questions):
            return CompletionStatus.INCOMPLETE

        ready = await self.session.fill_feedback_responses(activity, plan)
        if not ready:
            return CompletionStatus.INCOMPLETE

        return await self.session.submit_feedback(activity)

    async def verify(self, activity: Activity) -> CompletionStatus:
        if self.session is None:
            return CompletionStatus.UNKNOWN
        return await self.session.read_completion(activity)


class ViewHandler(ActivityHandler):
    """Open a view-only Moodle activity and verify server-side completion."""

    def __init__(self, session: MoodleSession | None = None):
        self.session = session

    async def execute(self, activity: Activity) -> CompletionStatus:
        if self.session is None or not activity.url:
            return CompletionStatus.INCOMPLETE

        await self.session.open(activity.url)
        return await self.session.read_completion(activity)

    async def verify(self, activity: Activity) -> CompletionStatus:
        if self.session is None:
            return CompletionStatus.UNKNOWN
        return await self.session.read_completion(activity)


class H5PHandler(ActivityHandler):
    """Open H5P, then trust only Moodle's authoritative completion state."""

    def __init__(self, session: MoodleSession | None = None):
        self.session = session

    async def execute(self, activity: Activity) -> CompletionStatus:
        if self.session is None or not activity.url:
            return CompletionStatus.INCOMPLETE

        await self.session.open(activity.url)
        return await self.session.read_completion(activity)

    async def verify(self, activity: Activity) -> CompletionStatus:
        if self.session is None:
            return CompletionStatus.UNKNOWN
        return await self.session.read_completion(activity)


class QuizHandler(ActivityHandler):
    """Run and verify a Moodle quiz without confusing attempt with passing."""

    def __init__(self, session: MoodleSession | None = None):
        self.session = session
        self.last_attempt = None

    async def execute(self, activity: Activity) -> CompletionStatus:
        if self.session is None or not activity.url:
            return CompletionStatus.INCOMPLETE

        attempt = await self.session.start_quiz_attempt(activity)
        self.last_attempt = attempt

        if not attempt.started:
            return CompletionStatus.INCOMPLETE
        if attempt.submitted:
            return self._status_from_attempt(activity, attempt)
        if not attempt.ready_to_submit:
            return CompletionStatus.INCOMPLETE

        submitted = await self.session.submit_quiz_attempt(activity, attempt)
        self.last_attempt = submitted
        return self._status_from_attempt(activity, submitted)

    async def verify(self, activity: Activity) -> CompletionStatus:
        if self.session is None:
            return CompletionStatus.UNKNOWN

        result = await self.session.read_quiz_result(activity)
        self.last_attempt = result
        return self._status_from_attempt(activity, result)

    @staticmethod
    def _status_from_attempt(activity: Activity, result) -> CompletionStatus:
        if result.passed:
            return CompletionStatus.PASSED

        needs_passing = any(
            "pass" in item.type.lower()
            or "passing" in item.type.lower()
            or str(item.metadata.get("condition", "")).lower() == "pass"
            for item in activity.requirements
        )

        if needs_passing:
            return CompletionStatus.INCOMPLETE
        if result.submitted:
            return CompletionStatus.COMPLETE
        return CompletionStatus.INCOMPLETE
