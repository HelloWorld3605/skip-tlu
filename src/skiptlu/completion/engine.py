from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from skiptlu.completion.execution_planner import ExecutionPlanner
from skiptlu.completion.planner import ProcessPlanner
from skiptlu.completion.resolver import CompletionResolver
from skiptlu.completion.verification import VerificationEngine
from skiptlu.models.activity import Activity, CompletionStatus
from skiptlu.models.process import AvailabilityState, ProcessState


class ActionStatus(str, Enum):
    NOT_STARTED = "not_started"
    EXECUTED = "executed"
    FAILED = "failed"
    BLOCKED = "blocked"


class VerificationStatus(str, Enum):
    VERIFIED_COMPLETE = "verified_complete"
    VERIFIED_INCOMPLETE = "verified_incomplete"
    UNKNOWN = "unknown"


@dataclass
class ExecutionResult:
    activity_id: int
    status_before: CompletionStatus
    status_after: CompletionStatus
    changed: bool
    message: str
    process_state: ProcessState | None = None
    action_status: ActionStatus = ActionStatus.NOT_STARTED
    verification_status: VerificationStatus = VerificationStatus.UNKNOWN
    evidence: dict[str, object] | None = None


@dataclass
class BatchExecutionResult:
    results: list[ExecutionResult]

    @property
    def completed(self) -> list[int]:
        return [
            item.activity_id
            for item in self.results
            if item.verification_status == VerificationStatus.VERIFIED_COMPLETE
        ]

    @property
    def blocked(self) -> list[int]:
        return [
            item.activity_id
            for item in self.results
            if item.action_status == ActionStatus.BLOCKED
        ]

    @property
    def failed(self) -> list[int]:
        return [
            item.activity_id
            for item in self.results
            if item.action_status == ActionStatus.FAILED
        ]


class CompletionEngine:
    """Gate execution with Moodle-derived process state and authoritative verification."""

    def __init__(
        self,
        router,
        resolver: CompletionResolver | None = None,
        planner: ProcessPlanner | None = None,
        execution_planner: ExecutionPlanner | None = None,
        verifier: VerificationEngine | None = None,
    ):
        self.router = router
        self.resolver = resolver or CompletionResolver()
        self.planner = planner or ProcessPlanner()
        self.execution_planner = execution_planner or ExecutionPlanner()
        session = getattr(router, "session", None)
        self.verifier = verifier or (VerificationEngine(session) if session is not None else None)

    async def process(
        self,
        activity: Activity,
        activities: list[Activity] | None = None,
        now: datetime | None = None,
    ) -> ExecutionResult:
        requirements = self.resolver.resolve(activity)
        activity.requirements = requirements

        before = activity.completion_status

        if before in {CompletionStatus.COMPLETE, CompletionStatus.PASSED}:
            return ExecutionResult(
                activity_id=activity.id,
                status_before=before,
                status_after=before,
                changed=False,
                message="Already complete; skipped.",
                action_status=ActionStatus.NOT_STARTED,
                verification_status=VerificationStatus.VERIFIED_COMPLETE,
            )

        known_activities = activities or [activity]
        by_id = {item.id: item for item in known_activities}
        by_id[activity.id] = activity

        process_state = self.planner.evaluate(activity, by_id, now=now)

        if process_state.availability != AvailabilityState.READY:
            return ExecutionResult(
                activity_id=activity.id,
                status_before=before,
                status_after=before,
                changed=False,
                message=process_state.reason
                or f"Activity is {process_state.availability.value}; execution skipped.",
                process_state=process_state,
                action_status=ActionStatus.BLOCKED,
            )

        handler = self.router.for_activity(activity)

        try:
            await handler.execute(activity)
        except Exception as exc:
            return ExecutionResult(
                activity_id=activity.id,
                status_before=before,
                status_after=before,
                changed=False,
                message=f"Handler execution failed: {exc}",
                process_state=process_state,
                action_status=ActionStatus.FAILED,
                verification_status=VerificationStatus.UNKNOWN,
            )

        try:
            if self.verifier is not None:
                verification = await self.verifier.verify(activity)
                verified = verification.status
            else:
                verified = await handler.verify(activity)
                from skiptlu.completion.verification import VerificationResult
                verification = VerificationResult(
                    status=verified,
                    evidence={"source": "handler_compatibility_fallback"},
                )
        except Exception as exc:
            return ExecutionResult(
                activity_id=activity.id,
                status_before=before,
                status_after=before,
                changed=False,
                message=f"Handler executed, but verification failed: {exc}",
                process_state=process_state,
                action_status=ActionStatus.EXECUTED,
                verification_status=VerificationStatus.UNKNOWN,
            )

        activity.completion_status = verified
        verification_status = (
            VerificationStatus.VERIFIED_COMPLETE
            if verified in {CompletionStatus.COMPLETE, CompletionStatus.PASSED}
            else (
                VerificationStatus.UNKNOWN
                if verified == CompletionStatus.UNKNOWN
                else VerificationStatus.VERIFIED_INCOMPLETE
            )
        )

        return ExecutionResult(
            activity_id=activity.id,
            status_before=before,
            status_after=verified,
            changed=(
                verified in {CompletionStatus.COMPLETE, CompletionStatus.PASSED}
                and verified != before
            ),
            message=(
                f"Processed by {handler.__class__.__name__}; "
                f"Moodle verification: {verification_status.value}."
            ),
            process_state=process_state,
            action_status=ActionStatus.EXECUTED,
            verification_status=verification_status,
            evidence=verification.evidence,
        )

    async def process_all(
        self,
        activities: list[Activity],
        now: datetime | None = None,
        *,
        max_rounds: int | None = None,
    ) -> BatchExecutionResult:
        if not activities:
            return BatchExecutionResult([])

        plan = self.execution_planner.build(activities)
        rounds = max_rounds or max(len(activities), 1)
        results: list[ExecutionResult] = []

        if plan.cycles:
            cycle_nodes = {node for cycle in plan.cycles for node in cycle}
            for activity in activities:
                if activity.id in cycle_nodes:
                    results.append(
                        ExecutionResult(
                            activity_id=activity.id,
                            status_before=activity.completion_status,
                            status_after=activity.completion_status,
                            changed=False,
                            message="Dependency cycle detected; execution skipped.",
                            action_status=ActionStatus.BLOCKED,
                        )
                    )

        ordered = [activity_id for activity_id in plan.ordered_activity_ids]
        by_id = {activity.id: activity for activity in activities}

        for _ in range(rounds):
            changed_any = False
            round_results: list[ExecutionResult] = []

            for activity_id in ordered:
                activity = by_id[activity_id]
                if activity.completion_status in {
                    CompletionStatus.COMPLETE,
                    CompletionStatus.PASSED,
                }:
                    continue

                result = await self.process(activity, activities, now=now)
                round_results.append(result)
                changed_any = changed_any or result.changed

            results.extend(round_results)

            if not changed_any:
                break

        return BatchExecutionResult(results)
