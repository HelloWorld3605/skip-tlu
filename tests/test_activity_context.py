from pathlib import Path

from skiptlu.models.activity import Activity, ModuleType
from skiptlu.tasks.context import ActivityContext


def test_activity_context_builds_from_moodle_payload():
    activity = Activity(
        id=51068,
        module=ModuleType.ASSIGNMENT,
        name="assignment",
    )
    context = ActivityContext.from_collected_data(
        activity,
        {
            "description": "Tạo bài Word",
            "instructions": ["Tải file BÀI LÀM", "Nộp file Word"],
            "attachments": [
                {"name": "BaiLam.docx", "url": "https://example.test/BaiLam.docx"},
                {"name": "Picture.jpg", "url": "https://example.test/Picture.jpg"},
            ],
            "completion": ["To do: Make a submission"],
        },
    )

    assert context.activity.id == 51068
    assert context.instructions == ("Tải file BÀI LÀM", "Nộp file Word")
    assert [item.name for item in context.attachments] == ["BaiLam.docx", "Picture.jpg"]
    assert context.attachments[0].url.endswith("BaiLam.docx")
    assert context.metadata["completion"] == ["To do: Make a submission"]
