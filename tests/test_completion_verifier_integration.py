import asyncio

from skiptlu.completion.engine import CompletionEngine
from skiptlu.completion.verification import VerificationResult
from skiptlu.handlers.base import ActivityHandler
from skiptlu.models.activity import Activity, CompletionStatus, ModuleType


class FakeHandler(ActivityHandler):
    async def execute(self, activity):
        return CompletionStatus.COMPLETE

    async def verify(self, activity):
        raise AssertionError("legacy handler.verify must not be used when verifier is configured")


class FakeRouter:
    session = object()

    def for_activity(self, activity):
        return FakeHandler()


class FakeVerifier:
    async def verify(self, activity):
        return VerificationResult(
            status=CompletionStatus.COMPLETE,
            evidence={"marker": "server"},
        )


def test_engine_prefers_verification_engine_over_handler_verify():
    async def run():
        engine = CompletionEngine(FakeRouter(), verifier=FakeVerifier())
        activity = Activity(
            id=1,
            module=ModuleType.LESSON,
            name="lesson",
            completion_status=CompletionStatus.INCOMPLETE,
        )

        result = await engine.process(activity)

        assert result.status_after == CompletionStatus.COMPLETE
        assert result.changed is True
        assert result.evidence == {"marker": "server"}

    asyncio.run(run())
