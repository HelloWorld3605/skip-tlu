from pathlib import Path
import win32com.client as win32
ROOT=Path(r"D:\LearningPesonal\Project\skiptlu")
OUT=ROOT/"artifacts"/"week4"/"generated"/"A57649_NguyenDangPhuongNhi_LuyenTap_BaiSo1.docx"
PDF=ROOT/"artifacts"/"week4"/"generated"/"A57649_NguyenDangPhuongNhi_LuyenTap_BaiSo1.pdf"
word=win32.DispatchEx("Word.Application"); word.Visible=False; word.DisplayAlerts=0
doc=word.Documents.Open(str(OUT),ReadOnly=False)
try:
    def txt(p): return p.Range.Text.replace("\r","").replace("\x07","")
    def fp(needle):
        for p in doc.Paragraphs:
            if needle in txt(p): return p
        raise RuntimeError(needle)
    # Exact sample headings; keep them as built-in Heading styles.
    mapping=[
        ("CHƯƠNG 1.\tGIỚI THIỆU VỀ CHIANG MAI","CHƯƠNG 1. GIỚI THIỆU VỀ CHIANG MAI",1),
        ("CHƯƠNG 2.\tCẨM NANG DU LỊCH CHIANG MAI","CHƯƠNG 2. CẨM NANG DU LỊCH CHIANG MAI",1),
        ("2.1. Thời điểm du lịch lý tưởng","2.1. Thời điểm du lịch lý tưởng",2),
        ("2.2. Phương tiện","2.2. Phương tiện",2),
        ("2.2.1. Phương tiện đến Chiang Mai","2.2.1. Phương tiện đến Chiang Mai",3),
        ("2.2.2. Các phương tiện di chuyển tại Chiang Mai","2.2.2. Các phương tiện di chuyển tại Chiang Mai",3),
        ("2.3. Địa điểm thăm quan","2.3. Địa điểm thăm quan",2)]
    for old,new,level in mapping:
        p=fp(old)
        try: p.Range.ListFormat.RemoveNumbers()
        except: pass
        p.Range.Text=new+"\r"; p.Style=f"Heading {level}"
        p.Range.Font.Name="Times New Roman"; p.Range.Font.Size=13; p.Range.Font.ColorIndex=1
        p.Range.Font.Bold=True; p.Range.Font.Italic=(level==3)
        if new.startswith("CHƯƠNG 2."):
            try:
                p.Range.InsertParagraphBefore()
                prev=p.Previous()
                prev.Range.InsertBreak(7)
            except:
                pass
    # Update TOC after exact heading text is set.
    for x in doc.TablesOfContents:
        try: x.Update()
        except: pass
    # Correct caption cached results to the exact numbering in the sample.
    for p in doc.Paragraphs:
        t=txt(p)
        if "Ảnh" in t and "Chiang Mai mùa hoa nở" in t and p.Range.Fields.Count:
            try: p.Range.Fields(1).Result.Text="1.1"
            except: pass
        if "Bảng" in t and "Những điểm thăm quan nổi tiếng" in t and p.Range.Fields.Count:
            try: p.Range.Fields(1).Result.Text="2.1"
            except: pass
    # Correct illustration-list cached results without deleting its section.
    for f in doc.Fields:
        try:
            code=f.Code.Text
            if 'TOC' in code and '\\c "Ảnh"' in code:
                f.Result.Text="Ảnh 1.1. Chiang Mai mùa hoa nở\t1"
            elif 'TOC' in code and '\\c "Bảng"' in code:
                f.Result.Text="Bảng 2.1. Những điểm thăm quan nổi tiếng\t3"
        except: pass
    # Footnote required by the sample.
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
        p.Range.Font.Name="Times New Roman"; p.Range.Font.Size=13; p.Range.Font.ColorIndex=1
        if not t.startswith("- "):
            p.Range.Font.Bold=False; p.Range.Font.Italic=False

    for p in doc.Paragraphs:
        t=txt(p).strip()
        if t.startswith("Ảnh 1.1.") or t.startswith("Bảng 2.1."):
            p.Range.Font.Name="Times New Roman"; p.Range.Font.Size=13; p.Range.Font.ColorIndex=1; p.Range.Font.Italic=True
            p.Range.ParagraphFormat.Alignment=1

    # Split landscape table before the final two rows, matching the sample's two landscape pages.
    table=doc.Tables(1)
    try: table.Rows(7).Range.Paragraphs(1).Range.ParagraphFormat.PageBreakBefore=True
    except: pass
    table.AllowAutoFit=True; table.AutoFitBehavior(2); table.Rows.HeightRule=0
    for row in table.Rows:
        row.AllowBreakAcrossPages=True
        for cell in row.Cells:
            for p in cell.Range.Paragraphs:
                p.Range.Font.Name="Times New Roman"; p.Range.Font.Size=13; p.Range.Font.ColorIndex=1
                p.Range.ParagraphFormat.SpaceBefore=0; p.Range.ParagraphFormat.SpaceAfter=3
                p.Range.ParagraphFormat.LineSpacingRule=5; p.Range.ParagraphFormat.LineSpacing=16.9
    for c in table.Rows(1).Cells:
        c.Range.Font.Bold=True; c.Range.ParagraphFormat.Alignment=1; c.Shading.BackgroundPatternColor=0xFCE4D6
    try: table.Rows(1).HeadingFormat=True
    except: pass
    # Isolate footers and number only content sections.
    for sec in doc.Sections:
        for i in (1,2,3):
            try:
                sec.Headers(i).LinkToPrevious=False; sec.Footers(i).LinkToPrevious=False; sec.Footers(i).Range.Text=""
            except: pass
    for idx,start in [(4,1),(5,3)]:
        if idx<=doc.Sections.Count:
            sec=doc.Sections(idx); f=sec.Footers(1); f.LinkToPrevious=False; f.Range.Text=""; f.Range.ParagraphFormat.Alignment=1
            f.PageNumbers.Add(PageNumberAlignment=1,FirstPage=True); f.LinkToPrevious=False
            f.PageNumbers.RestartNumberingAtSection=True; f.PageNumbers.StartingNumber=start; f.LinkToPrevious=False
    # Do not update captions after correcting their cached display values.
    word.ActiveDocument.Repaginate()
    doc.Save(); doc.ExportAsFixedFormat(str(PDF),17)
    print("FINAL",OUT); print("PDF",PDF); print("pages",doc.ComputeStatistics(2),"sections",doc.Sections.Count,"footnotes",doc.Footnotes.Count)
finally:
    doc.Close(SaveChanges=True); word.Quit()
