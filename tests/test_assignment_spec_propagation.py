import asyncio
from pathlib import Path

from skiptlu.artifacts.base import StaticArtifactProvider
from skiptlu.handlers.practical import AssignmentHandler
from skiptlu.models.activity import Activity, CompletionStatus, ModuleType
from skiptlu.models.artifact import Artifact, ArtifactKind
from skiptlu.client.session import AssignmentSubmission


def test_assignment_handler_passes_task_specification_to_provider(tmp_path):
    artifact_path = tmp_path / "artifact.docx"
    artifact_path.write_bytes(b"test")

    captured = {}

    class Provider:
        async def prepare(self, activity, specification=None):
            captured["specification"] = specification
            return Artifact(path=artifact_path, kind=ArtifactKind.DOCX)

    class Session:
        async def submit_assignment(self, activity, artifact):
            return AssignmentSubmission(
                activity_id=activity.id,
                has_submission=True,
                completion=CompletionStatus.COMPLETE,
                status_text="submitted",
            )

    from skiptlu.tasks.context import ActivityContext
    from skiptlu.tasks.specification import ArtifactType, PracticalTaskSpecification

    task = PracticalTaskSpecification(
        activity_id=51068,
        title="demo",
        artifact_type=ArtifactType.DOCX,
    )

    async def context_factory(activity):
        return ActivityContext(activity=activity)

    handler = AssignmentHandler(
        session=Session(),
        artifact_provider=Provider(),
        task_context_factory=context_factory,
        understanding_engine=type(
            "Engine",
            (),
            {"understand": lambda self, context: task},
        )(),
    )

    status = asyncio.run(
        handler.execute(
            Activity(id=51068, module=ModuleType.ASSIGNMENT, name="demo")
        )
    )

    assert status == CompletionStatus.COMPLETE
    assert captured["specification"] is task
