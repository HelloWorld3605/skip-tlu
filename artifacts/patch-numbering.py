from pathlib import Path
p=Path(r"D:\LearningPesonal\Project\skiptlu\src\skiptlu\artifacts\word.py")
s=p.read_text(encoding="utf-8")
s=s.replace(
'''def _new_numbering(doc):
    root = doc.part.numbering_part.element
''',
'''def _ensure_numbering_part(doc):
    from docx.opc.part import Part
    from docx.opc.packuri import PackURI
    from docx.opc.constants import RELATIONSHIP_TYPE as RT

    for rel in doc.part.rels.values():
        if rel.reltype == RT.NUMBERING:
            return rel.target_part

    content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"
    blob = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="{W_NS}">
  <w:abstractNum w:abstractNumId="0">
    <w:multiLevelType w:val="multilevel"/>
    <w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="decimal"/><w:lvlText w:val="CHƯƠNG %1."/><w:pStyle w:val="Heading1"/></w:lvl>
    <w:lvl w:ilvl="1"><w:start w:val="1"/><w:numFmt w:val="decimal"/><w:lvlText w:val="%1.%2."/><w:pStyle w:val="Heading2"/></w:lvl>
    <w:lvl w:ilvl="2"><w:start w:val="1"/><w:numFmt w:val="decimal"/><w:lvlText w:val="%1.%2.%3."/><w:pStyle w:val="Heading3"/></w:lvl>
  </w:abstractNum>
  <w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>
</w:numbering>""".encode("utf-8")
    part = Part(PackURI("/word/numbering.xml"), content_type, blob, doc.part.package)
    doc.part.relate_to(part, RT.NUMBERING)
    return part


def _new_numbering(doc):
    root = _ensure_numbering_part(doc).element
''')
p.write_text(s,encoding="utf-8")
print("patched")
