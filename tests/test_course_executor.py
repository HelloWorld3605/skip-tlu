import asyncio

from skiptlu.completion.course_executor import CourseExecutor
from skiptlu.completion.engine import CompletionEngine
from skiptlu.models.activity import Activity, CompletionStatus, ModuleType
from skiptlu.models.course import Course, CourseSection
from skiptlu.models.process import ActivityRestriction, RestrictionType


class FakeHandler:
    async def execute(self, activity):
        activity.completion_status = CompletionStatus.COMPLETE

    async def verify(self, activity):
        return CompletionStatus.COMPLETE


class FakeRouter:
    session = None

    def __init__(self):
        self.handler = FakeHandler()

    def for_activity(self, activity):
        return self.handler


def test_course_executor_flattens_sections_and_reports_completion():
    async def run():
        course = Course(
            id=1,
            name="Demo",
            sections=[
                CourseSection(
                    id=10,
                    name="Week 1",
                    activities=[
                        Activity(id=1, module=ModuleType.PAGE, name="A"),
                    ],
                ),
                CourseSection(
                    id=11,
                    name="Week 2",
                    activities=[
                        Activity(id=2, module=ModuleType.PAGE, name="B"),
                    ],
                ),
            ],
        )

        report = await CourseExecutor(CompletionEngine(FakeRouter())).run(course)

        assert report.completed == [1, 2]
        assert report.incomplete == []
        assert report.final_statuses == {
            1: CompletionStatus.COMPLETE,
            2: CompletionStatus.COMPLETE,
        }

    asyncio.run(run())


def test_course_executor_releases_dependency_chain_after_verification():
    async def run():
        course = Course(
            id=2,
            name="Dependency Demo",
            sections=[
                CourseSection(
                    id=20,
                    name="Week",
                    activities=[
                        Activity(id=1, module=ModuleType.PAGE, name="A"),
                        Activity(id=2, module=ModuleType.PAGE, name="B"),
                        Activity(id=3, module=ModuleType.PAGE, name="C"),
                    ],
                ),
            ],
        )
        activities = course.sections[0].activities
        activities[1].metadata["restrictions"] = [
            ActivityRestriction(
                type=RestrictionType.COMPLETION,
                source_activity_id=1,
                source_activity_name="A",
            )
        ]
        activities[2].metadata["restrictions"] = [
            ActivityRestriction(
                type=RestrictionType.COMPLETION,
                source_activity_id=2,
                source_activity_name="B",
            )
        ]

        report = await CourseExecutor(CompletionEngine(FakeRouter())).run(course)

        assert report.completed == [1, 2, 3]
        assert report.incomplete == []
        assert len(report.result.results) >= 3

    asyncio.run(run())
