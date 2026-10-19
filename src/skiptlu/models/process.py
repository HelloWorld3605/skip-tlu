from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AvailabilityState(str, Enum):
    READY = "ready"
    BLOCKED_BY_DEPENDENCY = "blocked_by_dependency"
    SCHEDULED = "scheduled"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


class RestrictionType(str, Enum):
    COMPLETION = "completion"
    GRADE = "grade"
    DATE = "date"
    UNKNOWN = "unknown"


class ActivityRestriction(BaseModel):
    type: RestrictionType
    source_activity_id: int | None = None
    source_activity_name: str | None = None
    required_status: str = "complete"
    metadata: dict[str, object] = Field(default_factory=dict)


class AvailabilityWindow(BaseModel):
    opens_at: datetime | None = None
    closes_at: datetime | None = None
    due_at: datetime | None = None


class ProcessState(BaseModel):
    activity_id: int
    availability: AvailabilityState
    unmet_restrictions: list[ActivityRestriction] = Field(default_factory=list)
    window: AvailabilityWindow | None = None
    reason: str | None = None


class ProcessSnapshot(BaseModel):
    """Point-in-time execution plan for all discovered activities."""

    generated_at: datetime
    states: dict[int, ProcessState] = Field(default_factory=dict)

    @property
    def ready(self) -> list[int]:
        return [
            activity_id
            for activity_id, state in self.states.items()
            if state.availability == AvailabilityState.READY
        ]

    @property
    def blocked(self) -> list[int]:
        return [
            activity_id
            for activity_id, state in self.states.items()
            if state.availability == AvailabilityState.BLOCKED_BY_DEPENDENCY
        ]

    @property
    def scheduled(self) -> list[int]:
        return [
            activity_id
            for activity_id, state in self.states.items()
            if state.availability == AvailabilityState.SCHEDULED
        ]

    @property
    def expired(self) -> list[int]:
        return [
            activity_id
            for activity_id, state in self.states.items()
            if state.availability == AvailabilityState.EXPIRED
        ]


class ProcessNode(BaseModel):
    activity_id: int
    activity_name: str
    status: str
    state: ProcessState


class DependencyGraph(BaseModel):
    """Resolved prerequisite graph.

    dependencies[target] contains activity IDs that must be satisfied first.
    """

    dependencies: dict[int, list[int]] = Field(default_factory=dict)

    def prerequisites_for(self, activity_id: int) -> list[int]:
        return self.dependencies.get(activity_id, [])

    def dependents_of(self, activity_id: int) -> list[int]:
        return [
            target
            for target, sources in self.dependencies.items()
            if activity_id in sources
        ]
