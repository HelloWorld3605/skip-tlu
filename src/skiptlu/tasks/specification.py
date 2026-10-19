from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

from skiptlu.tasks.content import ContentSpecification
from skiptlu.tasks.content_operations import ContentOperation, RegionContract
from skiptlu.tasks.layout import LayoutSpecification


class ArtifactType(str, Enum):
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    EXISTING = "existing"


class TaskRequirement(BaseModel):
    key: str
    description: str
    value: str | int | float | bool | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class ReferenceEvidence(BaseModel):
    source: Path
    kind: str
    facts: dict[str, object] = Field(default_factory=dict)


class PracticalTaskSpecification(BaseModel):
    activity_id: int
    title: str
    artifact_type: ArtifactType
    requirements: list[TaskRequirement] = Field(default_factory=list)
    source_files: list[Path] = Field(default_factory=list)
    content: ContentSpecification | None = None
    layout: LayoutSpecification | None = None
    content_operations: list[ContentOperation] = Field(default_factory=list)
    region_contracts: list[RegionContract] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)

    def has_requirement(self, key: str) -> bool:
        return any(item.key == key for item in self.requirements)
