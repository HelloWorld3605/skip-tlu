from pathlib import Path
from skiptlu.artifacts.word_backend import NativeWordBackend
from skiptlu.artifacts.word_renderer import *
from skiptlu.artifacts.word import _new_numbering, _configure_styles
from skiptlu.models.word_task import StudentInfo, WordTaskSpecification
from skiptlu.tasks.content import ContentFigure, ContentSection, ContentSpecification, ContentTable
from skiptlu.tasks.layout import default_word_layout

ROOT=Path(".").resolve()
doc=NativeWordBackend().open(ROOT/"artifacts/reference/BaiLam_LuyenTap_BaiSo1.docx")
content=ContentSpecification(title="Chiang Mai",sections=[ContentSection(level=1,title="GIỚI THIỆU VỀ CHIANG MAI"),ContentSection(level=1,title="CẨM NANG DU LỊCH CHIANG MAI"),ContentSection(level=2,title="Thời điểm du lịch lý tưởng")],figures=[ContentFigure(label="Ảnh",caption="Ảnh 1.1. Chiang Mai mùa hoa nở")],tables=[ContentTable(label="Bảng",caption="Bảng 2.1. Những điểm thăm quan nổi tiếng")],include_toc=True,include_landscape_section=True)
spec=WordTaskSpecification(activity_id=51068,title="Chiang Mai",template_path=ROOT/"artifacts/reference/BaiLam_LuyenTap_BaiSo1.docx",image_path=ROOT/"artifacts/reference/Picture_De1.jpg",output_dir=Path("artifacts/debug"),student=StudentInfo(name="TEST",student_id="T",major="K"),content_specification=content,layout_specification=default_word_layout(include_toc=True,include_landscape=True))
_configure_styles(doc,spec.layout_specification)
WordCoverRenderer().render(doc,spec); print("cover", [p.text for p in doc.paragraphs[:15]])
nid=_new_numbering(doc); ch=WordHeadingRenderer(nid).render(doc,spec); print("heading", [p.text for p in doc.paragraphs[:15]])
WordSectionRenderer(spec.layout_specification).apply_body_section(doc,ch); WordFigureRenderer().render(doc,spec); print("figure", [p.text for p in doc.paragraphs[:15]])
WordSectionRenderer(spec.layout_specification).apply_landscape_section(doc,next(p for p in doc.paragraphs if p.style.name=="Heading 2")); WordTableRenderer().render(doc,spec,ch); WordFootnoteRenderer().render(doc,spec); print("pre-toc", [p.text for p in doc.paragraphs[:20]])
WordTocRenderer().render(doc); print("toc", [p.text for p in doc.paragraphs[:20]], "HAS", "TOC" in doc.element.xml)
