from pathlib import Path
p=Path(r"D:\LearningPesonal\Project\skiptlu\artifacts\finalize-v9.py")
s=p.read_text(encoding="utf-8")
s=s.replace('p.Range.Font.Color=0', 'p.Range.Font.ColorIndex=1')
# Replace the unreliable page-break-before block with a break on the preceding body paragraph.
s=s.replace('''if new.startswith("CHƯƠNG 2."):
            p.Range.ParagraphFormat.PageBreakBefore=True
            rr=p.Range.Duplicate; rr.Collapse(1); rr.InsertBreak(7)''',
'''if new.startswith("CHƯƠNG 2."):
            try:
                prev=p.Previous()
                rr=prev.Range.Duplicate
                rr.Collapse(0)
                rr.InsertBreak(7)
            except:
                pass''')
# Make caption paragraphs italic and black after cached field-result correction.
needle='''    # Split landscape table before the final two rows, matching the sample's two landscape pages.'''
insert='''    for p in doc.Paragraphs:
        t=txt(p).strip()
        if t.startswith("Ảnh 1.1.") or t.startswith("Bảng 2.1."):
            p.Range.Font.Name="Times New Roman"; p.Range.Font.Size=13; p.Range.Font.ColorIndex=1; p.Range.Font.Italic=True
            p.Range.ParagraphFormat.Alignment=1

'''+needle
assert needle in s
p.write_text(s.replace(needle,insert),encoding="utf-8")
print("patched")
