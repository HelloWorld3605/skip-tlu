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
    # Remove any list numbering and restore the exact chapter/subheading text from the sample.
    exact=[
        ("CHƯƠNG 1.\tGIỚI THIỆU VỀ CHIANG MAI","CHƯƠNG 1. GIỚI THIỆU VỀ CHIANG MAI",1),
        ("CHƯƠNG 2.\tCẨM NANG DU LỊCH CHIANG MAI","CHƯƠNG 2. CẨM NANG DU LỊCH CHIANG MAI",1),
        ("2.1. Thời điểm du lịch lý tưởng","2.1. Thời điểm du lịch lý tưởng",2),
        ("2.2. Phương tiện","2.2. Phương tiện",2),
        ("2.2.1. Phương tiện đến Chiang Mai","2.2.1. Phương tiện đến Chiang Mai",3),
        ("2.2.2. Các phương tiện di chuyển tại Chiang Mai","2.2.2. Các phương tiện di chuyển tại Chiang Mai",3),
        ("2.3. Địa điểm thăm quan","2.3. Địa điểm thăm quan",2)]
    for old,new,level in exact:
        p=fp(old)
        try: p.Range.ListFormat.RemoveNumbers()
        except: pass
        p.Range.Text=new+"\r"; p.Style=f"Heading {level}"
        p.Range.Font.Name="Times New Roman"; p.Range.Font.Size=13; p.Range.Font.ColorIndex=0
        p.Range.Font.Bold=True; p.Range.Font.Italic=(level==3)
        p.Range.ParagraphFormat.PageBreakBefore=(new.startswith("CHƯƠNG 2."))
    # Rebuild TOC from the exact sample headings.
    for x in list(doc.TablesOfContents):
        try: x.Range.Delete()
        except: pass
    sec2=doc.Sections(2); h=fp("MỤC LỤC")
    r=sec2.Range.Duplicate; r.Start=h.Range.End; r.End=r.End-1
    if r.Start<r.End: r.Delete()
    ins=doc.Range(h.Range.End,h.Range.End); ins.InsertParagraphAfter(); ins=doc.Range(h.Range.End+1,h.Range.End+1)
    doc.TablesOfContents.Add(Range=ins,RightAlignPageNumbers=True,UseHeadingStyles=True,UpperHeadingLevel=1,LowerHeadingLevel=3,IncludePageNumbers=True,UseHyperlinks=True)
    # Static illustration list matching the sample's labels/numbers.
    for x in list(doc.TablesOfFigures):
        try: x.Range.Delete()
        except: pass
    sec3=doc.Sections(3); h=fp("DANH MỤC MINH HỌA")
    r=sec3.Range.Duplicate; r.Start=h.Range.End; r.End=r.End-1
    if r.Start<r.End: r.Delete()
    p=doc.Range(h.Range.End,h.Range.End).Paragraphs(1)
    p.Range.Text="Ảnh 1.1. Chiang Mai mùa hoa nở\t1\r"
    p.Range.Font.Name="Times New Roman"; p.Range.Font.Size=13
    p.Range.ParagraphFormat.TabStops.Add(500)
    p.Range.ParagraphFormat.TabStops.Add(450)
    p=doc.Range(sec3.Range.End-1,sec3.Range.End-1).Paragraphs(1)
    p.Range.Text="Bảng 2.1. Những điểm thăm quan nổi tiếng\t3\r"
    p.Range.Font.Name="Times New Roman"; p.Range.Font.Size=13
    # Replace automatic captions with exact sample captions.
    for needle in ["Ảnh 0.1. Chiang Mai mùa hoa nở","Ảnh 1.1. Chiang Mai mùa hoa nở","Bảng 0.1. Những điểm thăm quan nổi tiếng","Bảng 2.1. Những điểm thăm quan nổi tiếng"]:
        for p in list(doc.Paragraphs):
            if needle in txt(p):
                p.Range.Delete()
    pic=doc.InlineShapes(2)
    r=pic.Range.Duplicate; r.Collapse(0); r.InsertParagraphAfter(); r.Collapse(0)
    r.Text="Ảnh 1.1. Chiang Mai mùa hoa nở\r"
    r.Font.Name="Times New Roman"; r.Font.Size=13; r.Font.Italic=True
    r.ParagraphFormat.Alignment=1
    table=doc.Tables(1)
    r=table.Range.Duplicate; r.Collapse(1); r.InsertParagraphBefore()
    r=table.Range.Paragraphs(1).Range
    r.Text="Bảng 2.1. Những điểm thăm quan nổi tiếng\r"
    r.Font.Name="Times New Roman"; r.Font.Size=13; r.Font.Italic=True
    r.ParagraphFormat.Alignment=1
    # Split the table before row 7 so page 3 contains the first 5 data rows and page 4 the final 2.
    try:
        table.Rows(7).Range.Paragraphs(1).Range.ParagraphFormat.PageBreakBefore=True
    except: pass
    # Ensure table remains readable.
    table.AllowAutoFit=True; table.AutoFitBehavior(2); table.Rows.HeightRule=0
    for row in table.Rows:
        row.AllowBreakAcrossPages=True
        for cell in row.Cells:
            for p in cell.Range.Paragraphs:
                p.Range.Font.Name="Times New Roman"; p.Range.Font.Size=13; p.Range.Font.ColorIndex=0
                p.Range.ParagraphFormat.SpaceBefore=0; p.Range.ParagraphFormat.SpaceAfter=3
                p.Range.ParagraphFormat.LineSpacingRule=5; p.Range.ParagraphFormat.LineSpacing=16.9
    for c in table.Rows(1).Cells:
        c.Range.Font.Bold=True; c.Range.ParagraphFormat.Alignment=1; c.Shading.BackgroundPatternColor=0xFCE4D6
    try: table.Rows(1).HeadingFormat=True
    except: pass
    # Footer isolation.
    for sec in doc.Sections:
        for i in (1,2,3):
            try:
                sec.Headers(i).LinkToPrevious=False; sec.Footers(i).LinkToPrevious=False; sec.Footers(i).Range.Text=""
            except: pass
    for idx,start in [(4,1),(5,3)]:
        sec=doc.Sections(idx); f=sec.Footers(1); f.LinkToPrevious=False; f.Range.Text=""; f.Range.ParagraphFormat.Alignment=1
        f.PageNumbers.Add(PageNumberAlignment=1,FirstPage=True); f.LinkToPrevious=False
        f.PageNumbers.RestartNumberingAtSection=True; f.PageNumbers.StartingNumber=start; f.LinkToPrevious=False
    # Fields / pagination.
    for f in doc.Fields:
        try: f.Update()
        except: pass
    for x in doc.TablesOfContents:
        try: x.Update()
        except: pass
    word.ActiveDocument.Repaginate()
    doc.Save(); doc.ExportAsFixedFormat(str(PDF),17)
    print("FINAL",OUT); print("PDF",PDF); print("pages",doc.ComputeStatistics(2),"sections",doc.Sections.Count,"footnotes",doc.Footnotes.Count)
finally:
    doc.Close(SaveChanges=True); word.Quit()
