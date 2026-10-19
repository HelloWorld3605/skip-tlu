from skiptlu.completion.planner import ProcessPlanner
from skiptlu.models.activity import Activity, CompletionStatus, ModuleType
from skiptlu.models.process import (
    ActivityRestriction,
    AvailabilityState,
    RestrictionType,
)


def make_activity(activity_id: int, name: str, status=CompletionStatus.INCOMPLETE, **metadata):
    return Activity(
        id=activity_id,
        module=ModuleType.LESSON,
        name=name,
        completion_status=status,
        metadata=metadata,
    )


def test_snapshot_classifies_dependency_chain():
    lesson = make_activity(
        1,
        "Theory",
        CompletionStatus.COMPLETE,
    )
    assignment = make_activity(
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
    quiz = make_activity(
        3,
        "Quiz",
        restrictions=[
            ActivityRestriction(
                type=RestrictionType.COMPLETION,
                source_activity_id=2,
                source_activity_name="Practice",
            )
        ],
    )

    snapshot = ProcessPlanner().snapshot([lesson, assignment, quiz])

    assert snapshot.ready == [1, 2]
    assert snapshot.blocked == [3]
    assert snapshot.states[3].unmet_restrictions[0].source_activity_id == 2


def test_dependency_graph_exposes_prerequisites_and_dependents():
    lesson = make_activity(1, "Theory")
    assignment = make_activity(
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

    graph = ProcessPlanner().dependency_graph([lesson, assignment])

    assert graph.prerequisites_for(2) == [1]
    assert graph.dependents_of(1) == [2]


def test_passing_grade_restriction_requires_passed_state():
    source = make_activity(1, "Quiz", CompletionStatus.COMPLETE)
    target = make_activity(
        2,
        "Exam",
        restrictions=[
            ActivityRestriction(
                type=RestrictionType.GRADE,
                source_activity_id=1,
                source_activity_name="Quiz",
                required_status="passed",
            )
        ],
    )

    state = ProcessPlanner().evaluate(target, {1: source, 2: target})
    assert state.availability == AvailabilityState.BLOCKED_BY_DEPENDENCY

    source.completion_status = CompletionStatus.PASSED
    state = ProcessPlanner().evaluate(target, {1: source, 2: target})
    assert state.availability == AvailabilityState.READY
