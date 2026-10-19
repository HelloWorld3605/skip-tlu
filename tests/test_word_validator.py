from pathlib import Path

from skiptlu.artifacts.word import build_word_artifact
from skiptlu.artifacts.word_validator import WordValidator, validate_word_artifact
from skiptlu.models.word_task import StudentInfo, WordTaskSpecification
from skiptlu.tasks.content import ContentFigure, ContentSection, ContentSpecification, ContentTable
from skiptlu.tasks.layout import default_word_layout


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "artifacts" / "reference" / "BaiLam_LuyenTap_BaiSo1.docx"
IMAGE = ROOT / "artifacts" / "reference" / "Picture_De1.jpg"


def make_spec(tmp_path):
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
    return WordTaskSpecification(
        activity_id=51068,
        title="Chiang Mai",
        template_path=TEMPLATE,
        image_path=IMAGE,
        output_dir=tmp_path,
        student=StudentInfo(
            name="TEST STUDENT",
            student_id="TEST000",
            major="TÀI CHÍNH - NGÂN HÀNG",
        ),
        content_specification=content,
        layout_specification=default_word_layout(include_toc=True, include_landscape=True),
    )


def test_word_validator_is_a_first_class_component(tmp_path):
    spec = make_spec(tmp_path)
    artifact = build_word_artifact(spec)

    errors = WordValidator().validate(artifact.path, spec)

    assert errors == []


def test_word_validator_compatibility_function(tmp_path):
    spec = make_spec(tmp_path)
    artifact = build_word_artifact(spec)

    assert validate_word_artifact(artifact.path, spec) == []
