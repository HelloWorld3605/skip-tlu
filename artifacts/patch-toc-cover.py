from pathlib import Path
p=Path(r"D:\LearningPesonal\Project\skiptlu\src\skiptlu\artifacts\word_renderer.py")
s=p.read_text(encoding="utf-8")

# Replace cover renderer with anchor-based logic.
start=s.index("class WordCoverRenderer:")
end=s.index("\nclass WordTocRenderer:", start)
cover='''class WordCoverRenderer:
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
'''
s=s[:start]+cover+s[end:]

# Replace TOC renderer with cleanup + field at the end of the template TOC zone.
start=s.index("class WordTocRenderer:")
end=s.index("\nclass WordHeadingRenderer:", start)
toc='''class WordTocRenderer:
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

        # Remove static TOC entries from a converted PDF. The real content
        # headings are preserved later in the document and are now represented
        # by Heading 1/2/3 styles.
        all_paragraphs = list(doc.paragraphs)
        try:
            start_index = all_paragraphs.index(title) + 1
        except ValueError:
            start_index = 0
        first_real_heading = next(
            (
                i for i in range(start_index, len(all_paragraphs))
                if all_paragraphs[i].style.name in {"Heading 1", "Heading 2", "Heading 3"}
                and all_paragraphs[i].text.strip()
            ),
            None,
        )
        if first_real_heading is not None:
            for p in all_paragraphs[start_index:first_real_heading]:
                if p._p.getparent() is not None:
                    p._element.getparent().remove(p._element)

        toc = paragraph_after(title)
        add_field(
            toc,
            'TOC \\o "1-3" \\h \\z \\u',
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
        add_field(image_list, 'TOC \\h \\z \\c "Ảnh"', "Update image list")
        table_list = paragraph_after(image_list)
        add_field(table_list, 'TOC \\h \\z \\c "Bảng"', "Update table list")
'''
s=s[:start]+toc+s[end:]

# Render TOC last, after all structural mutations.
old='''        WordCoverRenderer().render(doc, spec)
        content = spec.content_specification
        if self.layout.include_toc or content.include_toc:
            WordTocRenderer().render(doc, spec)

        chapter1 = WordHeadingRenderer(numbering_id).render(doc, spec)
'''
new='''        WordCoverRenderer().render(doc, spec)
        content = spec.content_specification

        chapter1 = WordHeadingRenderer(numbering_id).render(doc, spec)
'''
s=s.replace(old,new)
old='''        WordFootnoteRenderer().render(doc, spec)
'''
new='''        WordFootnoteRenderer().render(doc, spec)

        if self.layout.include_toc or content.include_toc:
            WordTocRenderer().render(doc)
'''
s=s.replace(old,new)

p.write_text(s,encoding="utf-8")
print("patched")
