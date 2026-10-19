import asyncio

from skiptlu.handlers.simple import H5PHandler, ViewHandler
from skiptlu.models.activity import Activity, CompletionStatus, ModuleType


class FakeSession:
    def __init__(self, status=CompletionStatus.COMPLETE):
        self.status = status
        self.opened = []

    async def open(self, url):
        self.opened.append(url)
        return None

    async def read_completion(self, activity):
        return self.status


def test_view_handler_opens_and_verifies():
    async def run():
        session = FakeSession()
        handler = ViewHandler(session)
        activity = Activity(
            id=10,
            module=ModuleType.RESOURCE,
            name="Document",
            url="https://example.test/resource",
        )

        result = await handler.execute(activity)

        assert result == CompletionStatus.COMPLETE
        assert session.opened == ["https://example.test/resource"]

    asyncio.run(run())


def test_view_handler_does_not_claim_completion_when_moodle_does_not():
    async def run():
        session = FakeSession(CompletionStatus.INCOMPLETE)
        handler = ViewHandler(session)
        activity = Activity(
            id=11,
            module=ModuleType.PAGE,
            name="Page",
            url="https://example.test/page",
        )

        result = await handler.execute(activity)

        assert result == CompletionStatus.INCOMPLETE

    asyncio.run(run())


def test_h5p_handler_requires_authoritative_completion():
    async def run():
        session = FakeSession(CompletionStatus.INCOMPLETE)
        handler = H5PHandler(session)
        activity = Activity(
            id=12,
            module=ModuleType.H5P,
            name="Interactive",
            url="https://example.test/h5p",
        )

        result = await handler.execute(activity)

        assert result == CompletionStatus.INCOMPLETE
        assert session.opened == ["https://example.test/h5p"]

    asyncio.run(run())
