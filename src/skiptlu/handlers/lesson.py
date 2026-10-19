from skiptlu.client.session import MoodleSession
from skiptlu.handlers.base import ActivityHandler
from skiptlu.models.activity import Activity, CompletionStatus


class LessonHandler(ActivityHandler):
    """Traverse a Moodle Lesson until its final page, then verify completion."""

    def __init__(self, session: MoodleSession | None = None, max_pages: int = 200):
        self.session = session
        self.max_pages = max_pages

    async def execute(self, activity: Activity) -> CompletionStatus:
        if self.session is None:
            return CompletionStatus.INCOMPLETE

        if not activity.url:
            return CompletionStatus.INCOMPLETE

        page = await self.session.open(activity.url)

        for _ in range(self.max_pages):
            status = await self.session.read_completion(activity)
            if status in {CompletionStatus.COMPLETE, CompletionStatus.PASSED}:
                return status

            if page.is_final or not page.has_next:
                break

            page = await self.session.next_page()

        return await self.session.read_completion(activity)

    async def verify(self, activity: Activity) -> CompletionStatus:
        if self.session is None:
            return activity.completion_status
        return await self.session.read_completion(activity)
