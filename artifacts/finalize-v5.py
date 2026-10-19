from pathlib import Path
import win32com.client as win32

ROOT=Path(r"D:\LearningPesonal\Project\skiptlu")
OUT=ROOT/"artifacts"/"week4"/"generated"/"A57649_NguyenDangPhuongNhi_LuyenTap_BaiSo1.docx"
PDF=ROOT/"artifacts"/"week4"/"generated"/"A57649_NguyenDangPhuongNhi_LuyenTap_BaiSo1.pdf"

wdAlignCenter=1; wdCaptionPositionAbove=0; wdCaptionPositionBelow=1
wdListApplyToWholeList=0; wdWord10ListBehavior=2
word=win32.DispatchEx("Word.Application"); word.Visible=False; word.DisplayAlerts=0
doc=word.Documents.Open(str(OUT),ReadOnly=False)
try:
    def ptxt(p): return p.Range.Text.replace("\r","").replace("\x07","")
    def findp(needle):
        for p in doc.Paragraphs:
            if needle in ptxt(p): return p
        raise RuntimeError(needle)
    def caplabel(name):
        try: x=word.CaptionLabels(name)
        except: x=word.CaptionLabels.Add(name)
        x.IncludeChapterNumber=True; x.ChapterStyleLevel=1; x.NumberStyle=0; x.Separator=1
    # Independent headers/footers for every section.
    for sec in doc.Sections:
        for i in (1,2,3):
            try:
                sec.Headers(i).LinkToPrevious=False
                sec.Footers(i).LinkToPrevious=False
                sec.Footers(i).Range.Text=""
            except: pass

    # Heading font: exact black Times New Roman.
    for p in doc.Paragraphs:
        t=ptxt(p).strip()
        if t in ["GIỚI THIỆU VỀ CHIANG MAI","CẨM NANG DU LỊCH CHIANG MAI","Thời điểm du lịch lý tưởng","Phương tiện",
                 "Phương tiện đến Chiang Mai","Các phương tiện di chuyển tại Chiang Mai","Địa điểm thăm quan"]:
            level=1 if t in ["GIỚI THIỆU VỀ CHIANG MAI","CẨM NANG DU LỊCH CHIANG MAI"] else (3 if t in ["Phương tiện đến Chiang Mai","Các phương tiện di chuyển tại Chiang Mai"] else 2)
            p.Style=f"Heading {level}"
            p.Range.Font.Name="Times New Roman"; p.Range.Font.Size=13; p.Range.Font.ColorIndex=0
            p.Range.Font.Bold=(level in (1,2)); p.Range.Font.Italic=(level==3)
            if t=="CẨM NANG DU LỊCH CHIANG MAI": p.Range.ParagraphFormat.PageBreakBefore=True

    # Apply a real multilevel list 1., 1.1., 1.1.1. in heading order.
    headings=[]
    wanted={"GIỚI THIỆU VỀ CHIANG MAI":1,"CẨM NANG DU LỊCH CHIANG MAI":1,
            "Thời điểm du lịch lý tưởng":2,"Phương tiện":2,
            "Phương tiện đến Chiang Mai":3,"Các phương tiện di chuyển tại Chiang Mai":3,
            "Địa điểm thăm quan":2}
    for p in doc.Paragraphs:
        t=ptxt(p).strip()
        if t in wanted: headings.append((p,wanted[t]))
    template=word.ListGalleries(3).ListTemplates(2)
    template.ListLevels(1).NumberFormat="CHƯƠNG %1."
    template.ListLevels(2).NumberFormat="%1.%2."
    template.ListLevels(3).NumberFormat="%1.%2.%3."
    template.ListLevels(1).LinkedStyle="Heading 1"
    template.ListLevels(2).LinkedStyle="Heading 2"
    template.ListLevels(3).LinkedStyle="Heading 3"
    first=True
    for p,level in headings:
        p.Range.ListFormat.ApplyListTemplateWithLevel(
            ListTemplate=template,
            ContinuePreviousList=(False if first else True),
            ApplyTo=wdListApplyToWholeList,
            DefaultListBehavior=wdWord10ListBehavior,
            ApplyLevel=level)
        p.Range.ListFormat.ListLevelNumber=level
        first=False

    # Body text: black, TNR 13, non-bold/non-italic.
    heading_texts=set(wanted)
    for p in doc.Paragraphs:
        t=ptxt(p).strip()
        if not t or t in heading_texts or t in ["MỤC LỤC","DANH MỤC MINH HỌA","TIỂU LUẬN"]:
            continue
        if "BỘ GIÁO DỤC" in t or "TRƯỜNG ĐẠI HỌC" in t or "SINH VIÊN THỰC HIỆN" in t or "MÃ SINH VIÊN" in t or "NGÀNH:" in t or "HÀ NỘI" in t:
            continue
        if p.Range.Information(12): # in table
            continue
        p.Range.Font.Name="Times New Roman"; p.Range.Font.Size=13; p.Range.Font.ColorIndex=0
        if not t.startswith("- "): p.Range.Font.Bold=False; p.Range.Font.Italic=False

    # Real automatic captions.
    caplabel("Ảnh"); caplabel("Bảng")
    for needle in ["Ảnh 1.1. Chiang Mai mùa hoa nở","Bảng 2.1. Những điểm thăm quan nổi tiếng"]:
        try: findp(needle).Range.Delete()
        except: pass
    pic=doc.InlineShapes(2)
    try:
        pic.Range.InsertCaption(Label="Ảnh",Title=" Chiang Mai mùa hoa nở",Position=wdCaptionPositionBelow,ExcludeLabel=False)
    except: pass
    table=doc.Tables(1); table.Range.Select()
    word.Selection.InsertCaption(Label="Bảng",Title=" Những điểm thăm quan nổi tiếng",Position=wdCaptionPositionAbove,ExcludeLabel=False)

    # Try rounded picture + shadow.
    try:
        shp=pic.ConvertToShape()
        shp.AutoShapeType=5
        shp.Line.Visible=False
        shp.Shadow.Visible=True
        shp.Shadow.Blur=4; shp.Shadow.OffsetX=2; shp.Shadow.OffsetY=2
        pic=shp.ConvertToInlineShape()
    except: pass

    # Footnote.
    if doc.Footnotes.Count==0:
        p=findp("Chiang Mai được mệnh danh"); pos=ptxt(p).find("Lanna")
        doc.Footnotes.Add(doc.Range(p.Range.Start+pos+5,p.Range.Start+pos+5),Text="Một quốc gia cổ đại tồn tại từ TK 13 đến cuối TK 18")

    # Replace fake TOC on section 2 with a real TOC.
    sec2=doc.Sections(2); h2=findp("MỤC LỤC")
    r=sec2.Range.Duplicate; r.Start=h2.Range.End; r.End=r.End-1
    if r.Start<r.End: r.Delete()
    ins=doc.Range(h2.Range.End,h2.Range.End)
    ins.InsertParagraphAfter(); ins=doc.Range(h2.Range.End+1,h2.Range.End+1)
    doc.TablesOfContents.Add(Range=ins,RightAlignPageNumbers=True,UseHeadingStyles=True,
        UpperHeadingLevel=1,LowerHeadingLevel=3,IncludePageNumbers=True,UseHyperlinks=True)

    # Replace fake illustration list on section 3 with real lists.
    sec3=doc.Sections(3); h3=findp("DANH MỤC MINH HỌA")
    r=sec3.Range.Duplicate; r.Start=h3.Range.End; r.End=r.End-1
    if r.Start<r.End: r.Delete()
    ins=doc.Range(h3.Range.End,h3.Range.End); ins.InsertParagraphAfter(); ins=doc.Range(h3.Range.End+1,h3.Range.End+1)
    doc.TablesOfFigures.Add(Range=ins,Caption="Ảnh",IncludeLabel=True,RightAlignPageNumbers=True,UseHyperlinks=True)
    ins=doc.Range(sec3.Range.End-1,sec3.Range.End-1); ins.InsertParagraphAfter(); ins=doc.Range(sec3.Range.End-1,sec3.Range.End-1)
    doc.TablesOfFigures.Add(Range=ins,Caption="Bảng",IncludeLabel=True,RightAlignPageNumbers=True,UseHyperlinks=True)

    # TOC styles.
    for name in ["TOC 1","TOC 2","TOC 3"]:
        try:
            s=doc.Styles(name); s.Font.Name="Times New Roman"; s.Font.Size=13; s.Font.ColorIndex=0
            s.Font.Bold=(name!="TOC 3"); s.Font.Italic=(name=="TOC 3")
        except: pass

    # Page numbers only in section 4 and 5.
    for i,sec in enumerate(doc.Sections,1):
        for ft in (1,2,3):
            try:
                sec.Footers(ft).LinkToPrevious=False
                sec.Footers(ft).Range.Text=""
            except: pass
    for idx,start in [(4,1),(5,3)]:
        sec=doc.Sections(idx)
        f=sec.Footers(1)
        f.LinkToPrevious=False
        f.Range.Text=""
        f.Range.ParagraphFormat.Alignment=wdAlignCenter
        f.PageNumbers.Add(PageNumberAlignment=1,FirstPage=True)
        f.LinkToPrevious=False
        f.PageNumbers.RestartNumberingAtSection=True
        f.PageNumbers.StartingNumber=start
        f.LinkToPrevious=False

    # Ensure landscape table uses visible grid, readable spacing and repeated header.
    table=doc.Tables(1)
    # Make the landscape table readable and force it to flow across two pages like the sample.
    table.AllowAutoFit=True
    table.AutoFitBehavior(2)
    table.Rows.HeightRule=0
    for row in table.Rows:
        row.AllowBreakAcrossPages=True
    for row in table.Rows:
        for cell in row.Cells:
            for p in cell.Range.Paragraphs:
                p.Range.Font.Name="Times New Roman"; p.Range.Font.Size=13; p.Range.Font.ColorIndex=0
                p.Range.ParagraphFormat.SpaceBefore=0; p.Range.ParagraphFormat.SpaceAfter=3; p.Range.ParagraphFormat.LineSpacingRule=5; p.Range.ParagraphFormat.LineSpacing=16.9
    for c in table.Rows(1).Cells:
        c.Range.Font.Bold=True; c.Range.ParagraphFormat.Alignment=wdAlignCenter
        c.Shading.BackgroundPatternColor=0xFCE4D6
    try:
        table.Rows(1).HeadingFormat=True
    except: pass

    # Update all fields and repaginate.
    for f in doc.Fields:
        try: f.Update()
        except: pass
    for x in doc.TablesOfContents:
        try: x.Update()
        except: pass
    for x in doc.TablesOfFigures:
        try: x.Update()
        except: pass
    word.ActiveDocument.Repaginate()
    doc.Save(); doc.ExportAsFixedFormat(str(PDF),17)
    print("FINAL",OUT); print("PDF",PDF); print("sections",doc.Sections.Count,"pages",doc.ComputeStatistics(2),"footnotes",doc.Footnotes.Count)
finally:
    doc.Close(SaveChanges=True); word.Quit()
