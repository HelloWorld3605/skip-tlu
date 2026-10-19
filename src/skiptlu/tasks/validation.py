from dataclasses import dataclass
from skiptlu.models.artifact import Artifact
from skiptlu.tasks.specification import PracticalTaskSpecification

@dataclass(frozen=True)
class ValidationReport:
    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

class TaskArtifactValidator:
    """Generic safety gate before a generated artifact reaches Moodle."""

    def validate(self, artifact: Artifact, specification: PracticalTaskSpecification) -> ValidationReport:
        errors: list[str] = []
        if not artifact.path.is_file():
            errors.append("Artifact file does not exist")
        elif artifact.path.stat().st_size == 0:
            errors.append("Artifact file is empty")
        expected = specification.artifact_type.value
        if expected != "existing" and artifact.kind.value != expected:
            errors.append(f"Artifact kind mismatch: expected {expected}, got {artifact.kind.value}")
        return ValidationReport(valid=not errors, errors=tuple(errors))
