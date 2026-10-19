from pathlib import Path
from tempfile import TemporaryDirectory
from skiptlu.artifacts.word import build_word_artifact
from skiptlu.artifacts.word_backend import NativeWordBackend
from skiptlu.models.word_task import StudentInfo, WordTaskSpecification
from skiptlu.tasks.content import ContentFigure, ContentSection, ContentSpecification, ContentTable
from skiptlu.tasks.layout import default_word_layout

ROOT=Path(".").resolve()
TEMPLATE=ROOT/"artifacts/reference/BaiLam_LuyenTap_BaiSo1.docx"
IMAGE=ROOT/"artifacts/reference/Picture_De1.jpg"
content=ContentSpecification(
 title="Chiang Mai",
 sections=[ContentSection(level=1,title="GIỚI THIỆU VỀ CHIANG MAI"),ContentSection(level=1,title="CẨM NANG DU LỊCH CHIANG MAI"),ContentSection(level=2,title="Thời điểm du lịch lý tưởng")],
 figures=[ContentFigure(label="Ảnh",caption="Ảnh 1.1. Chiang Mai mùa hoa nở")],
 tables=[ContentTable(label="Bảng",caption="Bảng 2.1. Những điểm thăm quan nổi tiếng")],
 include_toc=True,include_landscape_section=True)
spec=WordTaskSpecification(activity_id=51068,title="Chiang Mai",template_path=TEMPLATE,image_path=IMAGE,output_dir=Path("artifacts/debug"),student=StudentInfo(name="TEST",student_id="T",major="K"),content_specification=content,layout_specification=default_word_layout(include_toc=True,include_landscape=True))
class X(NativeWordBackend):
 def save(self,document,output_path):
  print("BEFORE_SAVE_TOC","TOC" in document.element.xml)
  print("TOC_PARAS",[p.text for p in document.paragraphs if "MỤC LỤC" in p.text])
  super().save(document,output_path)
with TemporaryDirectory() as t:
 spec.output_dir=Path(t)
 build_word_artifact(spec,backend=X())
