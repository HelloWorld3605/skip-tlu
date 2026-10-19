from pathlib import Path
p=Path(r"D:\LearningPesonal\Project\skiptlu\artifacts\finalize-v9.py")
s=p.read_text(encoding="utf-8")
s=s.replace('p.Range.ParagraphFormat.PageBreakBefore=new.startswith("CHƯƠNG 2.")',
'''if new.startswith("CHƯƠNG 2."):
            p.Range.ParagraphFormat.PageBreakBefore=True
            rr=p.Range.Duplicate; rr.Collapse(1); rr.InsertBreak(7)''')
s=s.replace('p.Range.Font.Name="Times New Roman"; p.Range.Font.Size=13; p.Range.Font.ColorIndex=0',
            'p.Range.Font.Name="Times New Roman"; p.Range.Font.Size=13; p.Range.Font.Color=0')
# Insert footnote before footer handling.
needle='''    # Split landscape table before the final two rows, matching the sample's two landscape pages.'''
insert='''    # Footnote required by the sample.
    if doc.Footnotes.Count==0:
        p=fp("Chiang Mai được mệnh danh"); pos=txt(p).find("Lanna")
        doc.Footnotes.Add(doc.Range(p.Range.Start+pos+5,p.Range.Start+pos+5),Text="Một quốc gia cổ đại tồn tại từ TK 13 đến cuối TK 18")
    # Normalize body font/weight to match the sample.
    headings={"CHƯƠNG 1. GIỚI THIỆU VỀ CHIANG MAI","CHƯƠNG 2. CẨM NANG DU LỊCH CHIANG MAI",
               "2.1. Thời điểm du lịch lý tưởng","2.2. Phương tiện",
               "2.2.1. Phương tiện đến Chiang Mai","2.2.2. Các phương tiện di chuyển tại Chiang Mai",
               "2.3. Địa điểm thăm quan"}
    for p in doc.Paragraphs:
        t=txt(p).strip()
        if not t or t in headings or "MỤC LỤC" in t or "DANH MỤC" in t:
            continue
        if p.Range.Information(12):
            continue
        p.Range.Font.Name="Times New Roman"; p.Range.Font.Size=13; p.Range.Font.Color=0
        if not t.startswith("- "):
            p.Range.Font.Bold=False; p.Range.Font.Italic=False

'''+needle
assert needle in s
p.write_text(s.replace(needle,insert),encoding="utf-8")
print("patched")
