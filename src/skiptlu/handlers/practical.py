from dataclasses import dataclass
from pathlib import Path

from skiptlu.handlers.base import ActivityHandler
from skiptlu.models.activity import Activity, CompletionStatus
from skiptlu.tasks.context import ActivityContext
from skiptlu.tasks.specification import PracticalTaskSpecification
from skiptlu.tasks.understanding import TaskUnderstandingEngine
from skiptlu.tasks.validation import TaskArtifactValidator


@dataclass
class PracticalExecution:
    activity_id: int
    artifact_path: Path | None = None
    submission_created: bool = False
    submission_submitted: bool = False
    completion_verified: bool = False
    reason: str | None = None
    task_specification: PracticalTaskSpecification | None = None


class AssignmentHandler(ActivityHandler):
    def __init__(
        self,
        session=None,
        artifact_provider=None,
        artifact_registry=None,
        task_context_factory=None,
        understanding_engine=None,
        artifact_validator=None,
    ):
        self.session = session
        self.artifact_provider = artifact_provider
        self.artifact_registry = artifact_registry
        self.task_context_factory = task_context_factory
        self.understanding_engine = understanding_engine or TaskUnderstandingEngine()
        self.artifact_validator = artifact_validator or TaskArtifactValidator()
        self.last_execution: PracticalExecution | None = None

    async def execute(
        self,
        activity: Activity,
        artifact_path: Path | None = None,
    ) -> CompletionStatus:
        if self.session is None:
            self.last_execution = PracticalExecution(
                activity.id,
                artifact_path=artifact_path,
                reason="Moodle session adapter is not connected.",
            )
            return CompletionStatus.INCOMPLETE

        specification = None
        if self.task_context_factory is not None:
            context = await self.task_context_factory(activity)
            specification = self.understanding_engine.understand(context)
            provider = self.artifact_provider
            if self.artifact_registry is not None:
                provider = self.artifact_registry.for_task(specification, activity)
            if provider is not None:
                artifact_obj = await provider.prepare(activity, specification)
                artifact_path = artifact_obj.path
            else:
                artifact_obj = None
        else:
            artifact_obj = None
            provider = self.artifact_provider
            if artifact_path is None and provider is not None:
                artifact_obj = await provider.prepare(activity)
                artifact_path = artifact_obj.path

        if artifact_path is None:
            self.last_execution = PracticalExecution(
                activity.id,
                reason="Assignment requires a real artifact; none was supplied.",
                task_specification=specification,
            )
            return CompletionStatus.INCOMPLETE

        artifact = Path(artifact_path)
        if not artifact.is_file() or artifact.stat().st_size == 0:
            self.last_execution = PracticalExecution(
                activity.id,
                artifact_path=artifact,
                reason="Artifact does not exist or is empty.",
                task_specification=specification,
            )
            return CompletionStatus.INCOMPLETE

        if specification is not None and artifact_obj is not None:
            report = self.artifact_validator.validate(artifact_obj, specification)
            if not report.valid:
                self.last_execution = PracticalExecution(
                    activity.id,
                    artifact_path=artifact,
                    reason="; ".join(report.errors),
                    task_specification=specification,
                )
                return CompletionStatus.INCOMPLETE

        result = await self.session.submit_assignment(activity, artifact)
        self.last_execution = PracticalExecution(
            activity_id=activity.id,
            artifact_path=artifact,
            submission_created=result.has_submission,
            submission_submitted=result.has_submission,
            completion_verified=result.completion
            in {CompletionStatus.COMPLETE, CompletionStatus.PASSED},
            reason=result.status_text or None,
            task_specification=specification,
        )
        return result.completion

    async def verify(self, activity: Activity) -> CompletionStatus:
        if self.session is None:
            return CompletionStatus.INCOMPLETE
        result = await self.session.read_assignment_submission(activity)
        if result.has_submission and result.completion in {
            CompletionStatus.COMPLETE,
            CompletionStatus.PASSED,
        }:
            return result.completion
        return CompletionStatus.INCOMPLETE


PracticalHandler = AssignmentHandler
