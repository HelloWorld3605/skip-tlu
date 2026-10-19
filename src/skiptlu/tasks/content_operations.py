from __future__ import annotations

from pydantic import BaseModel, Field


class RegionContract(BaseModel):
    """Allow-list describing what the content layer may change in a template region."""

    region_id: str
    allowed_operations: set[str] = Field(default_factory=set)
    required: bool = True
    target_pattern: str | None = None
    max_occurrences: int = 1


class ContentOperation(BaseModel):
    """Deterministic content edit planned by the LLM/task understanding layer."""

    operation: str  # replace_text | replace_paragraph | insert_after | delete_paragraph
    target: str = ""
    value: str | None = None
    region_id: str | None = None
    occurrence: int | None = None
    required: bool = True
    metadata: dict[str, object] = Field(default_factory=dict)
