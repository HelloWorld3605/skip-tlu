import pytest

from skiptlu.completion.execution_planner import ExecutionPlanner
from skiptlu.models.activity import Activity, CompletionStatus, ModuleType
from skiptlu.models.process import ActivityRestriction, RestrictionType


def activity(activity_id, name, restrictions=()):
    return Activity(
        id=activity_id,
        module=ModuleType.LESSON,
        name=name,
        metadata={"restrictions": list(restrictions)},
    )


def restriction(source_id):
    return ActivityRestriction(
        type=RestrictionType.COMPLETION,
        source_activity_id=source_id,
    )


def test_execution_planner_orders_prerequisites_first():
    activities = [
        activity(3, "Exam", [restriction(2)]),
        activity(1, "Theory"),
        activity(2, "Practice", [restriction(1)]),
    ]

    plan = ExecutionPlanner().build(activities)

    assert plan.ordered_activity_ids == (1, 2, 3)
    assert plan.cycles == ()


def test_execution_planner_detects_dependency_cycle():
    activities = [
        activity(1, "A", [restriction(2)]),
        activity(2, "B", [restriction(1)]),
    ]

    plan = ExecutionPlanner().build(activities)

    assert plan.ordered_activity_ids == ()
    assert plan.cycles == ((1, 2, 1),)


def test_execution_planner_ignores_external_dependency_nodes():
    activities = [
        activity(1, "Local"),
        activity(2, "Target", [restriction(999)]),
    ]

    plan = ExecutionPlanner().build(activities)

    assert plan.ordered_activity_ids == (1, 2)
