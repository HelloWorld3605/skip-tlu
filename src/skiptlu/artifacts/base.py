from pathlib import Path
from typing import Protocol

from skiptlu.models.activity import Activity
from skiptlu.models.artifact import Artifact
from skiptlu.tasks.specification import PracticalTaskSpecification


class ArtifactProvider(Protocol):
    async def prepare(self, activity: Activity, specification: PracticalTaskSpecification | None = None) -> Artifact:
        ...


class StaticArtifactProvider:
    """Returns a prebuilt artifact for activities that require an existing file."""

    async def prepare(self, activity: Activity, specification: PracticalTaskSpecification | None = None) -> Artifact:
        return self.artifact

    def __init__(self, artifact: Artifact):
        self.artifact = artifact


class WordArtifactProvider:
    """Builds a Word artifact, then optionally applies an artifact enhancer."""

    def __init__(self, specification_factory, *, enhancer=None):
        self.specification_factory = specification_factory
        self.enhancer = enhancer

    async def prepare(
        self,
        activity: Activity,
        specification: PracticalTaskSpecification | None = None,
    ) -> Artifact:
        from skiptlu.artifacts.word import build_word_artifact, validate_word_artifact

        if specification is None:
            raise ValueError("WordArtifactProvider requires a PracticalTaskSpecification")

        spec = self.specification_factory(activity, specification)
        artifact = build_word_artifact(spec)

        if self.enhancer is not None:
            artifact = await self.enhancer.enhance(artifact, specification)

        errors = validate_word_artifact(artifact.path, spec)
        if errors:
            raise ValueError(
                "Generated Word artifact failed validation: " + "; ".join(errors)
            )
        return artifact
