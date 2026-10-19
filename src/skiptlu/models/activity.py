from enum import Enum
from pydantic import BaseModel, Field
from .process import ActivityRestriction

class ModuleType(str, Enum):
    LESSON = "lesson"
    QUIZ = "quiz"
    ASSIGNMENT = "assign"
    FEEDBACK = "feedback"
    RESOURCE = "resource"
    PAGE = "page"
    H5P = "h5pactivity"

class CompletionStatus(str, Enum):
    INCOMPLETE = "incomplete"
    COMPLETE = "complete"
    PASSED = "passed"
    UNKNOWN = "unknown"

class CompletionRequirement(BaseModel):
    type: str
    required: bool = True
    value: str | int | float | bool | None = None
    metadata: dict[str, object] = Field(default_factory=dict)

class Activity(BaseModel):
    id: int
    cmid: int | None = None
    module: ModuleType
    name: str
    url: str | None = None
    completion_status: CompletionStatus = CompletionStatus.UNKNOWN
    requirements: list[CompletionRequirement] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)

    @property
    def restrictions(self) -> list[ActivityRestriction]:
        return [
            item for item in self.metadata.get("restrictions", [])
            if isinstance(item, ActivityRestriction)
        ]
