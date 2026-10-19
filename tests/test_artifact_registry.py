from pathlib import Path

import asyncio

from skiptlu.artifacts.registry import ArtifactRegistry
from skiptlu.models.activity import Activity, ModuleType
from skiptlu.models.word_task import StudentInfo
from skiptlu.tasks.content import ContentFigure, ContentSection, ContentSpecification, ContentTable
from skiptlu.tasks.layout import default_word_layout
from skiptlu.tasks.specification import ArtifactType, PracticalTaskSpecification


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "artifacts" / "reference" / "BaiLam_LuyenTap_BaiSo1.docx"
IMAGE = ROOT / "artifacts" / "reference" / "Picture_De1.jpg"


def make_task():
    content = ContentSpecification(
        title="Chiang Mai",
        sections=[
            ContentSection(level=1, title="GIỚI THIỆU VỀ CHIANG MAI"),
            ContentSection(level=1, title="CẨM NANG DU LỊCH CHIANG MAI"),
            ContentSection(level=2, title="Thời điểm du lịch lý tưởng"),
            ContentSection(level=2, title="Phương tiện"),
            ContentSection(level=2, title="Địa điểm thăm quan"),
            ContentSection(level=3, title="Phương tiện đến Chiang Mai"),
            ContentSection(level=3, title="Các phương tiện di chuyển tại Chiang Mai"),
        ],
        figures=[ContentFigure(label="Ảnh", caption="Ảnh 1.1. Chiang Mai mùa hoa nở")],
        tables=[ContentTable(label="Bảng", caption="Bảng 2.1. Những điểm thăm quan nổi tiếng")],
        include_toc=True,
        include_landscape_section=True,
    )
    return PracticalTaskSpecification(
        activity_id=51068,
        title="Chiang Mai",
        artifact_type=ArtifactType.DOCX,
        source_files=[TEMPLATE, IMAGE],
        content=content,
        layout=default_word_layout(include_toc=True, include_landscape=True),
    )


def test_registry_maps_week4_to_word_provider(tmp_path):
    registry = ArtifactRegistry(
        project_root=ROOT,
        student=StudentInfo(
            name="TEST STUDENT",
            student_id="TEST000",
            major="TÀI CHÍNH - NGÂN HÀNG",
        ),
        output_dir=tmp_path,
    )
    activity = Activity(
        id=51068,
        module=ModuleType.ASSIGNMENT,
        name="week4",
    )

    provider = registry.for_task(make_task(), activity)
    assert provider is not None

    async def run():
        artifact = await provider.prepare(activity, make_task())
        assert artifact.path.exists()
        assert artifact.path.stat().st_size > 0

    asyncio.run(run())
