from __future__ import annotations

from typing import Protocol

from skiptlu.models.artifact import Artifact
from skiptlu.tasks.specification import PracticalTaskSpecification


class ArtifactEnhancer(Protocol):
    async def enhance(self, artifact: Artifact, specification: PracticalTaskSpecification) -> Artifact:
        ...


class NoOpArtifactEnhancer:
    async def enhance(self, artifact: Artifact, specification: PracticalTaskSpecification) -> Artifact:
        return artifact


class McpArtifactEnhancer:
    """Apply planned Word-MCP enhancements after native rendering."""

    def __init__(self, adapter, *, planner) -> None:
        self.adapter = adapter
        self.planner = planner

    async def enhance(
        self,
        artifact: Artifact,
        specification: PracticalTaskSpecification,
    ) -> Artifact:
        if artifact.path.suffix.lower() != ".docx":
            return artifact

        operations = self.planner.plan(specification)
        if operations:
            await self.adapter.enhance(artifact.path, operations)
        return artifact
