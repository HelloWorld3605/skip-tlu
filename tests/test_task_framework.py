from pathlib import Path

from skiptlu.models.activity import Activity, ModuleType
from skiptlu.tasks.context import ActivityAttachment, ActivityContext
from skiptlu.tasks.specification import ArtifactType
from skiptlu.tasks.understanding import TaskUnderstandingEngine
from skiptlu.tasks.validation import TaskArtifactValidator
from skiptlu.models.artifact import Artifact, ArtifactKind


def test_task_understanding_extracts_docx_context():
    activity = Activity(id=51068, module=ModuleType.ASSIGNMENT, name="Word practice")
    context = ActivityContext(
        activity=activity,
        description="Thực hành Microsoft Word",
        instructions=("Tạo mục lục", "Chèn hình ảnh"),
        attachments=(
            ActivityAttachment("File BÀI LÀM", url="https://example.test/BaiLam_LuyenTap_BaiSo1.docx"),
            ActivityAttachment("Picture.jpg", Path("Picture.jpg")),
        ),
    )

    spec = TaskUnderstandingEngine().understand(context)

    assert spec.artifact_type == ArtifactType.DOCX
    assert len(spec.requirements) == 2
    assert len(spec.source_files) == 1


def test_generic_validator_blocks_missing_artifact(tmp_path):
    activity = Activity(id=51068, module=ModuleType.ASSIGNMENT, name="Word practice")
    context = ActivityContext(activity=activity, metadata={"artifact_type": "docx"})
    spec = TaskUnderstandingEngine().understand(context)

    artifact = Artifact(
        path=tmp_path / "missing.docx",
        kind=ArtifactKind.DOCX,
    )
    report = TaskArtifactValidator().validate(artifact, spec)

    assert not report.valid
    assert "does not exist" in report.errors[0]


def test_generic_validator_accepts_matching_artifact(tmp_path):
    path = tmp_path / "answer.docx"
    path.write_bytes(b"not-empty")
    spec = TaskUnderstandingEngine().understand(
        ActivityContext(
            activity=Activity(id=51068, module=ModuleType.ASSIGNMENT, name="Word"),
            metadata={"artifact_type": "docx"},
        )
    )
    report = TaskArtifactValidator().validate(
        Artifact(path=path, kind=ArtifactKind.DOCX),
        spec,
    )
    assert report.valid
