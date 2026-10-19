import asyncio

from skiptlu.client.session import SessionPage
from skiptlu.handlers.lesson import LessonHandler
from skiptlu.models.activity import Activity, CompletionStatus, ModuleType


class FakeSession:
    def __init__(self):
        self.pages = [
            SessionPage("lesson?page=1", has_next=True),
            SessionPage("lesson?page=2", has_next=True),
            SessionPage("lesson?page=3", is_final=True),
        ]
        self.index = 0
        self.next_calls = 0

    async def open(self, url):
        return self.pages[0]

    async def next_page(self):
        self.next_calls += 1
        self.index += 1
        return self.pages[self.index]

    async def read_completion(self, activity):
        if self.index >= 2:
            return CompletionStatus.COMPLETE
        return CompletionStatus.INCOMPLETE

    async def close(self):
        pass


def test_lesson_handler_traverses_until_server_completion():
    async def run():
        session = FakeSession()
        handler = LessonHandler(session=session)

        activity = Activity(
            id=51014,
            module=ModuleType.LESSON,
            name="lesson",
            url="https://example.test/mod/lesson/view.php?id=51014",
        )

        result = await handler.execute(activity)
        assert result == CompletionStatus.COMPLETE
        assert session.next_calls == 2

    asyncio.run(run())


def test_lesson_handler_does_not_claim_completion_without_verification():
    async def run():
        class NoCompletion(FakeSession):
            async def read_completion(self, activity):
                return CompletionStatus.INCOMPLETE

        session = NoCompletion()
        handler = LessonHandler(session=session, max_pages=2)

        activity = Activity(
            id=51014,
            module=ModuleType.LESSON,
            name="lesson",
            url="https://example.test/mod/lesson/view.php?id=51014",
        )

        result = await handler.execute(activity)
        assert result == CompletionStatus.INCOMPLETE

    asyncio.run(run())
