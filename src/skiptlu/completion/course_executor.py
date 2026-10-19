from dataclasses import dataclass, field
from datetime import datetime

from skiptlu.completion.engine import BatchExecutionResult, CompletionEngine
from skiptlu.completion.planner import ProcessPlanner
from skiptlu.models.activity import Activity, CompletionStatus
from skiptlu.models.course import Course


@dataclass
class CourseExecutionReport:
    course_id: int
    course_name: str
    result: BatchExecutionResult
    final_statuses: dict[int, CompletionStatus]
    blocked_reasons: dict[int, str] = field(default_factory=dict)

    @property
    def completed(self) -> list[int]:
        return [
            activity_id
            for activity_id, status in self.final_statuses.items()
            if status in {CompletionStatus.COMPLETE, CompletionStatus.PASSED}
        ]

    @property
    def incomplete(self) -> list[int]:
        return [
            activity_id
            for activity_id, status in self.final_statuses.items()
            if status not in {CompletionStatus.COMPLETE, CompletionStatus.PASSED}
        ]


class CourseExecutor:
    """Execute a discovered Moodle course as a dependency-aware process."""

    def __init__(
        self,
        engine: CompletionEngine,
        planner: ProcessPlanner | None = None,
    ):
        self.engine = engine
        self.planner = planner or ProcessPlanner()

    async def run(
        self,
        course: Course,
        now: datetime | None = None,
        *,
        max_rounds: int | None = None,
    ) -> CourseExecutionReport:
        activities = course.activities
        result = await self.engine.process_all(
            activities,
            now=now,
            max_rounds=max_rounds,
        )

        states = self.planner.snapshot(activities, now=now)
        blocked_reasons = {
            activity_id: state.reason
            for activity_id, state in states.states.items()
            if state.reason
        }

        return CourseExecutionReport(
            course_id=course.id,
            course_name=course.name,
            result=result,
            final_statuses={
                activity.id: activity.completion_status
                for activity in activities
            },
            blocked_reasons=blocked_reasons,
        )
