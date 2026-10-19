from datetime import datetime, timedelta, timezone

from skiptlu.completion.planner import ProcessPlanner
from skiptlu.models.activity import Activity, CompletionStatus, ModuleType
from skiptlu.models.process import (
    ActivityRestriction,
    AvailabilityState,
    RestrictionType,
)

def activity(activity_id: int, status=CompletionStatus.INCOMPLETE, **metadata):
    return Activity(
        id=activity_id,
        module=ModuleType.LESSON,
        name=f"A{activity_id}",
        completion_status=status,
        metadata=metadata,
    )

def test_blocks_when_completion_prerequisite_is_incomplete():
    source = activity(1)
    target = activity(
        2,
        restrictions=[
            ActivityRestriction(
                type=RestrictionType.COMPLETION,
                source_activity_id=1,
                source_activity_name="A1",
            )
        ],
    )
    state = ProcessPlanner().evaluate(target, {1: source, 2: target})
    assert state.availability == AvailabilityState.BLOCKED_BY_DEPENDENCY
    assert state.unmet_restrictions[0].source_activity_id == 1

def test_ready_when_prerequisite_is_complete():
    source = activity(1, CompletionStatus.COMPLETE)
    target = activity(
        2,
        restrictions=[
            ActivityRestriction(
                type=RestrictionType.COMPLETION,
                source_activity_id=1,
            )
        ],
    )
    state = ProcessPlanner().evaluate(target, {1: source, 2: target})
    assert state.availability == AvailabilityState.READY

def test_scheduled_before_open():
    target = activity(
        2,
        opens_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    state = ProcessPlanner().evaluate(target, {2: target})
    assert state.availability == AvailabilityState.SCHEDULED

def test_expired_after_close():
    target = activity(
        2,
        closes_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    state = ProcessPlanner().evaluate(target, {2: target})
    assert state.availability == AvailabilityState.EXPIRED
