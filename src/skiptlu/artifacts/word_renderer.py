from __future__ import annotations

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

from skiptlu.artifacts.content_controller import WordContentController
from skiptlu.artifacts.word_support import (
    caption,
    insert_section_before,
    page_number,
    paragraph_after,
    replace_paragraph,
)
from skiptlu.models.word_task import WordTaskSpecification
from skiptlu.tasks.content import ContentTable
from skiptlu.tasks.layout import LayoutSpecification


class WordCoverRenderer:
    def render(self, doc: Document, spec: WordTaskSpecification) -> None:
        content = spec.content_specification
        cover = content.cover if content else None

        paragraphs = doc.paragraphs

        def first_contains(value: str):
            return next((p for p in paragraphs if value.casefold() in p.text.casefold()), None)

        if cover:
            if cover.institution:
                p = first_contains("BỘ GIÁO DỤC") or (paragraphs[0] if paragraphs else None)
                if p: replace_paragraph(p, cover.institution)
            if cover.organization:
                p = first_contains("TRƯỜNG ĐẠI HỌC") or (paragraphs[1] if len(paragraphs) > 1 else None)
                if p: replace_paragraph(p, cover.organization)
            if cover.document_type:
                p = first_contains("TIỂU LUẬN") or first_contains("BÁO CÁO")
                if p: replace_paragraph(p, cover.document_type)

        # If the converted template already has editable student placeholders,
        # replace them. Otherwise insert the three student lines before the
        # existing cover footer, without disturbing the TOC.
        labels = (
            ("SINH VIÊN THỰC HIỆN:", spec.student.name),
            ("MÃ SINH VIÊN:", spec.student.student_id),
            ("NGÀNH:", spec.student.major),
        )
        missing = []
        for label, value in labels:
            p = first_contains(label)
            if p:
                replace_paragraph(p, f"{label} {value}")
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                for run in p.runs:
                    run.font.size = Pt(13)
                    run.bold = True
            else:
                missing.append((label, value))

        if missing:
            footer = first_contains("HÀ NỘI -") or first_contains("HANOI -")
            if footer:
                anchor = footer
                for label, value in missing:
                    p = anchor.insert_paragraph_before(
                        f"{label} {value}",
                    )
                    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                    p.paragraph_format.space_after = Pt(4)
                    for run in p.runs:
                        run.font.name = "Times New Roman"
                        run.font.size = Pt(13)
                        run.bold = True

        footer_value = cover.footer if cover else None
        footer = first_contains("HÀ NỘI -") or first_contains("HANOI -")
        if footer:
            replace_paragraph(
                footer,
                footer_value or f"HÀ NỘI - {spec.student.year}",
            )
            footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
            footer.paragraph_format.space_before = Pt(110)
            for run in footer.runs:
                run.font.size = Pt(13)
                run.bold = True

class WordTocRenderer:
    def render(self, doc: Document) -> None:
        from skiptlu.artifacts.word_support import add_field

        title = next(
            (p for p in doc.paragraphs if p.text.strip() == "MỤC LỤC"),
            None,
        )
        if title is None:
            return

        replace_paragraph(title, "MỤC LỤC")
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title.paragraph_format.space_after = Pt(18)
        for run in title.runs:
            run.font.name = "Times New Roman"
            run.font.size = Pt(14)
            run.bold = True

        toc = paragraph_after(title)
        add_field(
            toc,
            r'TOC \\o "1-3" \\h \\z \\u',
            "Update TOC",
        )

        illustration = next(
            (p for p in doc.paragraphs if p.text.strip() == "DANH MỤC MINH HỌA"),
            None,
        )
        if illustration is None:
            return

        replace_paragraph(illustration, "DANH MỤC MINH HỌA")
        illustration.alignment = WD_ALIGN_PARAGRAPH.CENTER
        illustration.paragraph_format.space_after = Pt(18)
        for run in illustration.runs:
            run.font.name = "Times New Roman"
            run.font.size = Pt(14)
            run.bold = True

        image_list = paragraph_after(illustration)
        add_field(image_list, r'TOC \\h \\z \\c "Ảnh"', "Update image list")
        table_list = paragraph_after(image_list)
        add_field(table_list, r'TOC \\h \\z \\c "Bảng"', "Update table list")

class WordHeadingRenderer:
    def __init__(self, numbering_id: int):
        self.numbering_id = numbering_id

    def render(self, doc: Document, spec: WordTaskSpecification) -> object:
        from skiptlu.artifacts.word import _clean_heading, _number

        h1 = {_clean_heading(item) for item in spec.derived_headings(1)}
        h2 = {_clean_heading(item) for item in spec.derived_headings(2)}
        h3 = {_clean_heading(item) for item in spec.derived_headings(3)}
        chapter1 = None

        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            clean = _clean_heading(text)
            if clean in h1:
                replace_paragraph(paragraph, clean)
                paragraph.style = "Heading 1"
                _number(paragraph, self.numbering_id, 0)
                chapter1 = chapter1 or paragraph
            elif clean in h2:
                replace_paragraph(paragraph, clean)
                paragraph.style = "Heading 2"
                _number(paragraph, self.numbering_id, 1)
            elif clean in h3:
                replace_paragraph(paragraph, clean)
                paragraph.style = "Heading 3"
                _number(paragraph, self.numbering_id, 2)
            elif text.startswith("- "):
                replace_paragraph(paragraph, text[2:])
                paragraph.style = "Style Trừ"

        if chapter1 is None:
            raise ValueError("Chapter 1 was not found in the supplied template")
        return chapter1


class WordFigureRenderer:
    def render(self, doc: Document, spec: WordTaskSpecification) -> None:
        content = spec.content_specification
        figure = content.figures[0] if content and content.figures else None

        if figure is None:
            figure_caption = next(
                (item for item in spec.derived_captions() if item.strip().startswith("Ảnh")),
                None,
            )
            if figure_caption:
                figure = type("_Figure", (), {
                    "label": figure_caption.split(".", 1)[0].strip(),
                    "caption": figure_caption,
                })()

        if figure is None or not spec.image_path.is_file():
            return

        target = next(
            (p for p in doc.paragraphs if p.style.name == "Heading 1" and p.text.strip()),
            next((p for p in doc.paragraphs if p.style.name == "Normal" and p.text.strip()), None),
        )
        if target is None:
            return

        image_p = paragraph_after(target)
        image_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        image_p.add_run().add_picture(str(spec.image_path), width=Cm(11))
        caption_text = (
            figure.caption.split(".", 2)[-1].strip()
            if "." in figure.caption
            else figure.caption
        )
        caption(doc, image_p, figure.label, caption_text, "1.1")


class WordSectionRenderer:
    def __init__(self, layout: LayoutSpecification):
        self.layout = layout

    def apply_body_section(self, doc: Document, chapter1) -> None:
        section = insert_section_before(doc, chapter1)
        self._configure(section, WD_ORIENT.PORTRAIT)
        page_number(section)

    def apply_landscape_section(self, doc: Document, heading) -> None:
        section = insert_section_before(doc, heading)
        self._configure(section, WD_ORIENT.LANDSCAPE)
        section.page_width = Cm(29.7)
        section.page_height = Cm(21)
        page_number(section)

    def _configure(self, section, orientation):
        section.orientation = orientation
        section.top_margin = Cm(self.layout.page.top_cm)
        section.bottom_margin = Cm(self.layout.page.bottom_cm)
        section.left_margin = Cm(self.layout.page.left_cm)
        section.right_margin = Cm(self.layout.page.right_cm)
        section.header_distance = Cm(self.layout.page.header_cm)
        section.footer_distance = Cm(self.layout.page.footer_cm)


class WordTableRenderer:
    def find_landscape_heading(self, doc: Document, fallback):
        if not doc.tables:
            return fallback
        table = doc.tables[0]
        table_node = table._tbl
        for paragraph in reversed(doc.paragraphs):
            if paragraph._p.getparent().index(paragraph._p) < table_node.getparent().index(table_node):
                if paragraph.style.name == "Heading 2" and paragraph.text.strip():
                    return paragraph
        return fallback

    def render(self, doc: Document, spec: WordTaskSpecification, landscape_heading) -> None:
        content = spec.content_specification
        requirement = content.tables[0] if content and content.tables else None

        if requirement is None:
            table_caption = next(
                (item for item in spec.derived_captions() if item.strip().startswith("Bảng")),
                None,
            )
            if table_caption:
                requirement = ContentTable(
                    label=table_caption.split(".", 1)[0].strip(),
                    caption=table_caption,
                )

        if requirement is None or not doc.tables:
            return

        table = doc.tables[0]
        table_node = table._tbl
        caption_anchor = table_node.getprevious()
        if caption_anchor is not None:
            from docx.text.paragraph import Paragraph
            anchor = Paragraph(caption_anchor, table._parent)
            text = (
                requirement.caption.split(".", 2)[-1].strip()
                if "." in requirement.caption
                else requirement.caption
            )
            if not anchor.text.strip().startswith("Bảng"):
                caption(doc, anchor, requirement.label, text, "2.1")


class WordFootnoteRenderer:
    def render(self, doc: Document, spec: WordTaskSpecification) -> None:
        content = spec.content_specification
        if not content or not content.include_footnotes:
            return

        anchor = next(
            (p for p in doc.paragraphs if p.style.name == "Normal" and p.text.strip()),
            None,
        )
        if anchor is not None:
            from skiptlu.artifacts.word_support import footnote_reference
            footnote_reference(anchor)


class WordRenderer:
    def __init__(self, layout: LayoutSpecification):
        self.layout = layout

    def render(self, doc: Document, spec: WordTaskSpecification, numbering_id: int) -> None:
        WordCoverRenderer().render(doc, spec)
        content = spec.content_specification
        chapter1 = WordHeadingRenderer(numbering_id).render(doc, spec)
        WordSectionRenderer(self.layout).apply_body_section(doc, chapter1)
        WordFigureRenderer().render(doc, spec)

        landscape_heading = chapter1
        if self.layout.landscape_before_level is not None or content.include_landscape_section:
            candidates = [
                p for p in doc.paragraphs
                if p.style.name == "Heading 2" and p.text.strip()
            ]
            if candidates:
                landscape_heading = candidates[0]
            elif doc.tables:
                # The supplied exercise template may not contain a Heading 2
                # immediately before the required table. Use the paragraph
                # directly preceding the table as the section anchor so the
                # landscape section is still deterministic.
                table_node = doc.tables[0]._tbl
                previous = table_node.getprevious()
                if previous is not None:
                    from docx.text.paragraph import Paragraph
                    landscape_heading = Paragraph(previous, doc.tables[0]._parent)
            WordSectionRenderer(self.layout).apply_landscape_section(doc, landscape_heading)
            WordTableRenderer().render(doc, spec, landscape_heading)

        WordFootnoteRenderer().render(doc, spec)

        if self.layout.include_toc or content.include_toc:
            WordTocRenderer().render(doc)
