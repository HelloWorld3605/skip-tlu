from pathlib import Path

from skiptlu.models.activity import Activity, ModuleType
from skiptlu.tasks.context import ActivityAttachment, ActivityContext


def test_context_can_attach_downloaded_paths(tmp_path):
    activity = Activity(id=51068, module=ModuleType.ASSIGNMENT, name="Word")
    context = ActivityContext(
        activity=activity,
        attachments=(
            ActivityAttachment("File BÀI LÀM", url="https://example.test/BaiLam.docx"),
            ActivityAttachment("Missing", url="https://example.test/missing.pdf"),
        ),
    )

    downloaded = tmp_path / "BaiLam.docx"
    downloaded.write_bytes(b"docx")
    updated = context.with_attachment_paths(
        {"https://example.test/BaiLam.docx": downloaded}
    )

    assert updated.attachments[0].path == downloaded
    assert updated.attachments[1].path is None
    assert context.attachments[0].path is None


def test_reference_filename_uses_url_extension():
    from skiptlu.client.playwright import PlaywrightMoodleSession

    assert PlaywrightMoodleSession._reference_filename(
        "File BÀI LÀM",
        "https://example.test/files/BaiLam_LuyenTap_BaiSo1.docx",
    ).endswith("_BaiLam_LuyenTap_BaiSo1.docx")
