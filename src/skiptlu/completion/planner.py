from datetime import datetime, timezone

from skiptlu.models.activity import Activity, CompletionStatus
from skiptlu.models.process import (
    ActivityRestriction,
    AvailabilityState,
    AvailabilityWindow,
    DependencyGraph,
    ProcessSnapshot,
    ProcessState,
)


class ProcessPlanner:
    """Builds a server-state-aware execution plan before handlers run."""

    def evaluate(
        self,
        activity: Activity,
        activities_by_id: dict[int, Activity],
        now: datetime | None = None,
    ) -> ProcessState:
        now = now or datetime.now(timezone.utc)
        unmet: list[ActivityRestriction] = []

        for restriction in activity.restrictions:
            source = activities_by_id.get(restriction.source_activity_id or -1)
            if not self._restriction_satisfied(restriction, source):
                unmet.append(restriction)

        window = AvailabilityWindow(
            opens_at=self._datetime_metadata(activity, "opens_at"),
            closes_at=self._datetime_metadata(activity, "closes_at"),
            due_at=self._datetime_metadata(activity, "due_at"),
        )

        if unmet:
            return ProcessState(
                activity_id=activity.id,
                availability=AvailabilityState.BLOCKED_BY_DEPENDENCY,
                unmet_restrictions=unmet,
                window=window,
                reason="One or more prerequisite activities are incomplete.",
            )

        comparison_now = self._comparison_now(now, window)

        if window.opens_at is not None and comparison_now < window.opens_at:
            return ProcessState(
                activity_id=activity.id,
                availability=AvailabilityState.SCHEDULED,
                window=window,
                reason="Activity has not opened yet.",
            )

        if window.closes_at is not None and comparison_now > window.closes_at:
            return ProcessState(
                activity_id=activity.id,
                availability=AvailabilityState.EXPIRED,
                window=window,
                reason="Activity is past its closing time.",
            )

        return ProcessState(
            activity_id=activity.id,
            availability=AvailabilityState.READY,
            window=window,
        )

    def snapshot(
        self,
        activities: list[Activity],
        now: datetime | None = None,
    ) -> ProcessSnapshot:
        now = now or datetime.now(timezone.utc)
        by_id = {activity.id: activity for activity in activities}

        return ProcessSnapshot(
            generated_at=now,
            states={
                activity.id: self.evaluate(activity, by_id, now)
                for activity in activities
            },
        )

    def dependency_graph(self, activities: list[Activity]) -> DependencyGraph:
        dependencies: dict[int, list[int]] = {}

        for activity in activities:
            source_ids = [
                restriction.source_activity_id
                for restriction in activity.restrictions
                if restriction.source_activity_id is not None
            ]
            if source_ids:
                dependencies[activity.id] = list(dict.fromkeys(source_ids))

        return DependencyGraph(dependencies=dependencies)

    @staticmethod
    def _restriction_satisfied(
        restriction: ActivityRestriction,
        source: Activity | None,
    ) -> bool:
        if source is None:
            return False

        required = restriction.required_status.lower()
        status = source.completion_status

        if restriction.type.value == "grade" or required in {"passed", "pass"}:
            return status == CompletionStatus.PASSED

        return status in {
            CompletionStatus.COMPLETE,
            CompletionStatus.PASSED,
        }

    @staticmethod
    def _datetime_metadata(
        activity: Activity,
        key: str,
    ) -> datetime | None:
        value = activity.metadata.get(key)
        return value if isinstance(value, datetime) else None

    @staticmethod
    def _comparison_now(now: datetime, window: AvailabilityWindow) -> datetime:
        """Normalize naive Moodle timestamps and aware runtime timestamps.

        The HTML parser may only know a wall-clock time from Moodle. Until the
        server timezone is explicitly configured, compare naive timestamps as
        wall-clock values rather than raising a naive/aware TypeError.
        """
        window_values = (window.opens_at, window.closes_at, window.due_at)
        has_naive_window = any(
            value is not None and value.tzinfo is None
            for value in window_values
        )
        if has_naive_window and now.tzinfo is not None:
            return now.replace(tzinfo=None)
        return now
