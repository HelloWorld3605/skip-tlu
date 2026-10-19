from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class ArtifactKind(str, Enum):
    EXISTING = "existing"
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"


class Artifact(BaseModel):
    path: Path
    kind: ArtifactKind
    metadata: dict[str, object] = Field(default_factory=dict)
