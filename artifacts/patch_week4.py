from pathlib import Path
p=Path(r"D:\LearningPesonal\Project\skiptlu\src\skiptlu\tasks\understanding.py")
s=p.read_text(encoding="utf-8")
s=s.replace(
"        return ContentSpecification(\n            title=context.activity.name,",
"        include_landscape = include_landscape or bool(unique_tables)\n\n        return ContentSpecification(\n            title=context.activity.name,"
)
p.write_text(s,encoding="utf-8")

p=Path(r"D:\LearningPesonal\Project\skiptlu\src\skiptlu\artifacts\word_renderer.py")
s=p.read_text(encoding="utf-8")
old='''        table = doc.tables[0]
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
            caption(doc, anchor, requirement.label, text, "2.1")
'''
new='''        table = doc.tables[0]
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
'''
assert old in s
p.write_text(s.replace(old,new),encoding="utf-8")
