from pathlib import Path
p=Path(r"D:\LearningPesonal\Project\skiptlu\src\skiptlu\artifacts\word_support.py")
s=p.read_text(encoding="utf-8")
a=s.index("def insert_section_before")
b=s.index("def caption",a)
block=(
"def insert_section_before(doc, paragraph):\n"
"    from docx.oxml import OxmlElement\n"
"    from docx.oxml.ns import qn\n"
"    ppr = paragraph._p.get_or_add_pPr()\n"
"    existing = ppr.find(qn(\"w:sectPr\"))\n"
"    if existing is not None:\n"
"        ppr.remove(existing)\n"
"    sect = OxmlElement(\"w:sectPr\")\n"
"    ppr.append(sect)\n"
"    return doc.sections[-1]\n\n\n"
)
p.write_text(s[:a]+block+s[b:],encoding="utf-8")
print("fixed")
