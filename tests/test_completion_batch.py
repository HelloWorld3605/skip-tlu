import asyncio

from skiptlu.completion.engine import CompletionEngine, VerificationStatus
from skiptlu.handlers.base import ActivityHandler
from skiptlu.models.activity import Activity, CompletionStatus, ModuleType
from skiptlu.models.process import ActivityRestriction, RestrictionType


class ChainHandler(ActivityHandler):
    async def execute(self, activity):
        return CompletionStatus.COMPLETE

    async def verify(self, activity):
        return CompletionStatus.COMPLETE


class Router:
    def __init__(self):
        self.handler = ChainHandler()

    def for_activity(self, activity):
        return self.handler


def test_process_all_unlocks_dependency_after_verified_completion():
    async def run():
        prerequisite = Activity(
            id=1,
            module=ModuleType.LESSON,
            name="Theory",
            completion_status=CompletionStatus.INCOMPLETE,
        )
        dependent = Activity(
            id=2,
            module=ModuleType.ASSIGNMENT,
            name="Practice",
            completion_status=CompletionStatus.INCOMPLETE,
            metadata={
                "restrictions": [
                    ActivityRestriction(
                        type=RestrictionType.COMPLETION,
                        source_activity_id=1,
                        source_activity_name="Theory",
                    )
                ]
            },
        )

        result = await CompletionEngine(Router()).process_all(
            [prerequisite, dependent]
        )

        assert prerequisite.completion_status == CompletionStatus.COMPLETE
        assert dependent.completion_status == CompletionStatus.COMPLETE
        assert result.completed == [1, 2]

    asyncio.run(run())


def test_process_all_stops_when_no_progress_is_made():
    async def run():
        class IncompleteHandler(ActivityHandler):
            async def execute(self, activity):
                return CompletionStatus.INCOMPLETE

            async def verify(self, activity):
                return CompletionStatus.INCOMPLETE

        class IncompleteRouter:
            def for_activity(self, activity):
                return IncompleteHandler()

        activity = Activity(
            id=1,
            module=ModuleType.LESSON,
            name="Lesson",
        )

        result = await CompletionEngine(IncompleteRouter()).process_all([activity])

        assert activity.completion_status == CompletionStatus.INCOMPLETE
        assert result.results[0].verification_status == VerificationStatus.VERIFIED_INCOMPLETE

    asyncio.run(run())
