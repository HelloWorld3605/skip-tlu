import asyncio

from skiptlu.completion.engine import (
    ActionStatus,
    CompletionEngine,
    VerificationStatus,
)
from skiptlu.handlers.base import ActivityHandler
from skiptlu.models.activity import Activity, CompletionStatus, ModuleType


class FakeHandler(ActivityHandler):
    def __init__(self, executed_status=CompletionStatus.COMPLETE, verification_status=None, fail_execute=False):
        self.executed_status = executed_status
        self.verification_status = verification_status
        self.fail_execute = fail_execute
        self.executed = False

    async def execute(self, activity):
        self.executed = True
        if self.fail_execute:
            raise RuntimeError("boom")
        return self.executed_status

    async def verify(self, activity):
        if self.verification_status is not None:
            return self.verification_status
        return self.executed_status


class FakeRouter:
    def __init__(self, handler):
        self.handler = handler

    def for_activity(self, activity):
        return self.handler


def test_engine_distinguishes_execution_from_verified_completion():
    async def run():
        handler = FakeHandler(
            executed_status=CompletionStatus.COMPLETE,
            verification_status=CompletionStatus.INCOMPLETE,
        )
        engine = CompletionEngine(FakeRouter(handler))
        activity = Activity(
            id=1,
            module=ModuleType.RESOURCE,
            name="resource",
            completion_status=CompletionStatus.INCOMPLETE,
        )

        result = await engine.process(activity)

        assert result.action_status == ActionStatus.EXECUTED
        assert result.verification_status == VerificationStatus.VERIFIED_INCOMPLETE
        assert result.status_after == CompletionStatus.INCOMPLETE
        assert handler.executed

    asyncio.run(run())


def test_engine_marks_handler_exception_as_failed():
    async def run():
        handler = FakeHandler(fail_execute=True)
        engine = CompletionEngine(FakeRouter(handler))
        activity = Activity(
            id=1,
            module=ModuleType.RESOURCE,
            name="resource",
        )

        result = await engine.process(activity)

        assert result.action_status == ActionStatus.FAILED
        assert result.verification_status == VerificationStatus.UNKNOWN
        assert result.status_after == CompletionStatus.UNKNOWN

    asyncio.run(run())
