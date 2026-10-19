import asyncio
from datetime import datetime, timedelta, timezone

from skiptlu.completion.engine import CompletionEngine
from skiptlu.handlers.router import HandlerRouter
from skiptlu.models.activity import Activity, CompletionStatus, ModuleType
from skiptlu.models.process import ActivityRestriction, RestrictionType


def lesson(activity_id: int, name: str, status=CompletionStatus.INCOMPLETE, **metadata):
    return Activity(
        id=activity_id,
        module=ModuleType.LESSON,
        name=name,
        completion_status=status,
        metadata=metadata,
    )


def test_engine_blocks_activity_until_prerequisite_is_complete():
    source = lesson(1, "Theory")
    target = lesson(
        2,
        "Practice",
        restrictions=[
            ActivityRestriction(
                type=RestrictionType.COMPLETION,
                source_activity_id=1,
                source_activity_name="Theory",
            )
        ],
    )

    result = asyncio.run(
        CompletionEngine(HandlerRouter()).process(
            target,
            activities=[source, target],
        )
    )

    assert result.process_state is not None
    assert result.process_state.availability.value == "blocked_by_dependency"
    assert result.status_after == CompletionStatus.INCOMPLETE
    assert result.changed is False


def test_engine_allows_ready_activity_but_does_not_fake_completion():
    activity = lesson(1, "Theory")

    result = asyncio.run(CompletionEngine(HandlerRouter()).process(activity))

    assert result.process_state is not None
    assert result.process_state.availability.value == "ready"
    assert result.status_after == CompletionStatus.INCOMPLETE
    assert result.changed is False


def test_engine_blocks_scheduled_activity():
    activity = lesson(
        1,
        "Scheduled",
        opens_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )

    result = asyncio.run(CompletionEngine(HandlerRouter()).process(activity))

    assert result.process_state is not None
    assert result.process_state.availability.value == "scheduled"
    assert result.status_after == CompletionStatus.INCOMPLETE
