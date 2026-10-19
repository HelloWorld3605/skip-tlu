from pathlib import Path
import win32com.client as win32

ROOT=Path(r"D:\LearningPesonal\Project\skiptlu")
WEEK=ROOT/"artifacts"/"week4"
SRC=next(WEEK.glob("BaiLam_LuyenTap_BaiSo1.docx"))
IMG=WEEK/"Picture_De1.jpg"
OUT=WEEK/"generated"/"A57649_NguyenDangPhuongNhi_LuyenTap_BaiSo1.docx"
PDF=WEEK/"generated"/"A57649_NguyenDangPhuongNhi_LuyenTap_BaiSo1.pdf"
OUT.parent.mkdir(exist_ok=True)

wdCollapseEnd=0; wdCollapseStart=1
wdSectionBreakNextPage=2; wdPageBreak=7
wdAlignCenter=1; wdAlignLeft=0; wdAlignJustify=3
wdOrientPortrait=0; wdOrientLandscape=1
wdCaptionPositionAbove=0; wdCaptionPositionBelow=1
wdHeaderFooterPrimary=1
wdFieldPage=33

def text(p): return p.Range.Text.replace("\r","").replace("\x07","")

def findp(doc, needle):
    for p in doc.Paragraphs:
        if needle in text(p):
            return p
    raise RuntimeError("not found: "+needle)

def set_a4(sec, landscape=False):
    ps=sec.PageSetup
    ps.Orientation=wdOrientLandscape if landscape else wdOrientPortrait
    ps.PageWidth=841.89 if landscape else 595.28
    ps.PageHeight=595.28 if landscape else 841.89
    ps.TopMargin=56.7; ps.BottomMargin=56.7
    ps.LeftMargin=85.05; ps.RightMargin=42.52
    ps.HeaderDistance=28.35; ps.FooterDistance=28.35

def unlink(sec):
    for i in (1,2,3):
        try:
            sec.Headers(i).LinkToPrevious=False
            sec.Footers(i).LinkToPrevious=False
        except: pass

def clear_footer(sec):
    try:
        unlink(sec)
        sec.Footers(1).Range.Text=""
    except: pass

def add_page_number(sec,start):
    unlink(sec)
    f=sec.Footers(1)
    f.Range.Text=""
    f.Range.ParagraphFormat.Alignment=wdAlignCenter
    f.Range.Fields.Add(f.Range, wdFieldPage)
    f.PageNumbers.RestartNumberingAtSection=True
    f.PageNumbers.StartingNumber=start

def caption_style(doc):
    try: s=doc.Styles("Caption")
    except: s=doc.Styles.Add("Caption")
    s.Font.Name="Times New Roman"; s.Font.NameAscii="Times New Roman"
    s.Font.Size=13; s.Font.Italic=True; s.Font.ColorIndex=0
    s.ParagraphFormat.Alignment=wdAlignCenter
    s.ParagraphFormat.SpaceBefore=6; s.ParagraphFormat.SpaceAfter=6
    s.ParagraphFormat.LineSpacingRule=5; s.ParagraphFormat.LineSpacing=1.3

def caplabel(doc,name):
    try: x=doc.Application.CaptionLabels(name)
    except: x=doc.Application.CaptionLabels.Add(name)
    x.IncludeChapterNumber=True
    x.ChapterStyleLevel=1
    x.NumberStyle=0
    x.Separator=1
    return x

word=win32.DispatchEx("Word.Application")
word.Visible=False; word.DisplayAlerts=0
src=None; doc=None
try:
    src=word.Documents.Open(str(SRC),ReadOnly=True)
    doc=word.Documents.Add()
    set_a4(doc.Sections(1),False)

    # Copy cover exactly from original: paragraphs 1-9, including the supplied university logo.
    cover_end=src.Paragraphs(9).Range.End
    doc.Range(0,0).FormattedText=src.Range(0,cover_end).FormattedText

    # Replace student placeholders.
    reps={
        "HỌ TÊN CỦA SINH VIÊN":"NGUYỄN ĐẶNG PHƯƠNG NHI",
        "MÃ CỦA SINH VIÊN":"A57649",
        "NGÀNH CỦA SINH VIÊN":"KẾ TOÁN",
    }
    for a,b in reps.items():
        r=doc.Content.Duplicate; f=r.Find; f.Text=a; f.Replacement.Text=b; f.Execute(Replace=2)

    # Cover typography and tab alignment.
    for needle in ["BỘ GIÁO DỤC VÀ ĐÀO TẠO","TRƯỜNG ĐẠI HỌC THĂNG LONG",
                   "TIỂU LUẬN","CHIANG MAI ĐÓA HỒNG PHƯƠNG BẮC XỨ CHÙA VÀNG",
                   "SINH VIÊN THỰC HIỆN:","MÃ SINH VIÊN:","NGÀNH:","HÀ NỘI - 2026"]:
        try: findp(doc,needle).Alignment=wdAlignCenter
        except: pass
    for needle,size,bold in [
        ("BỘ GIÁO DỤC",13,False),("TRƯỜNG ĐẠI HỌC",13,True),
        ("TIỂU LUẬN",20,True),("CHIANG MAI ĐÓA HỒNG",17,True),
        ("SINH VIÊN THỰC HIỆN:",13,True),("MÃ SINH VIÊN:",13,True),
        ("NGÀNH:",13,True),("HÀ NỘI - 2026",13,True)]:
        p=findp(doc,needle); p.Range.Font.Name="Times New Roman"; p.Range.Font.Size=size; p.Range.Font.Bold=bold

    # Student lines: use one real tab, never manual spaces.
    for needle in ["SINH VIÊN THỰC HIỆN:","MÃ SINH VIÊN:","NGÀNH:"]:
        p=findp(doc,needle)
        s=text(p)
        s=s.replace("\t"," ").strip()
        label,value=s.split(":",1)
        p.Range.Text=label.upper()+":\t"+value.strip().upper()+"\r"
        p.Alignment=wdAlignCenter
        p.Range.Font.Name="Times New Roman"; p.Range.Font.Size=13; p.Range.Font.Bold=True
        p.Range.ParagraphFormat.TabStops.ClearAll()
        p.Range.ParagraphFormat.TabStops.Add(283.5)

    # Logo
    if doc.InlineShapes.Count:
        logo=doc.InlineShapes(1); logo.Width=58; logo.Height=58
        logo.Range.ParagraphFormat.Alignment=wdAlignCenter

    # Remove any existing footer and page number from cover section.
    clear_footer(doc.Sections(1))

    # Page 2: TOC.
    r=doc.Content.Characters.Last.Duplicate; r.Collapse(wdCollapseEnd); r.InsertBreak(wdPageBreak)
    r=doc.Content.Characters.Last.Duplicate; r.Collapse(wdCollapseEnd)
    p=r.Paragraphs(1); p.Range.Text="MỤC LỤC\r"; p.Alignment=wdAlignCenter
    p.Range.Font.Name="Times New Roman"; p.Range.Font.Size=13; p.Range.Font.Bold=True
    r=p.Range.Duplicate; r.Collapse(wdCollapseEnd); r.InsertParagraphAfter()
    toc_range=doc.Range(r.End+1,r.End+1)
    doc.TablesOfContents.Add(Range=toc_range,RightAlignPageNumbers=True,UseHeadingStyles=True,
        UpperHeadingLevel=1,LowerHeadingLevel=3,IncludePageNumbers=True,UseHyperlinks=True,HidePageNumbersInWeb=True)

    # Page 3: illustration list.
    r=doc.Content.Characters.Last.Duplicate; r.Collapse(wdCollapseEnd); r.InsertBreak(wdPageBreak)
    r=doc.Content.Characters.Last.Duplicate; r.Collapse(wdCollapseEnd)
    p=r.Paragraphs(1); p.Range.Text="DANH MỤC MINH HỌA\r"; p.Alignment=wdAlignCenter
    p.Range.Font.Name="Times New Roman"; p.Range.Font.Size=13; p.Range.Font.Bold=True
    r=p.Range.Duplicate; r.Collapse(wdCollapseEnd); r.InsertParagraphAfter()
    caplabel(doc,"Ảnh"); caplabel(doc,"Bảng")
    fig_range=doc.Range(r.End+1,r.End+1)
    doc.TablesOfFigures.Add(Range=fig_range,Caption="Ảnh",IncludeLabel=True,RightAlignPageNumbers=True,UseHyperlinks=True)
    fig_range.End=doc.TablesOfFigures(1).Range.End
    fig_range.InsertParagraphAfter()
    tabfig=doc.Range(fig_range.End+1,fig_range.End+1)
    doc.TablesOfFigures.Add(Range=tabfig,Caption="Bảng",IncludeLabel=True,RightAlignPageNumbers=True,UseHyperlinks=True)

    # Section break: content starts page 1.
    r=doc.Content.Characters.Last.Duplicate; r.Collapse(wdCollapseEnd); r.InsertBreak(wdSectionBreakNextPage)
    content_sec=doc.Sections(doc.Sections.Count)
    set_a4(content_sec,False)
    clear_footer(content_sec)
    add_page_number(content_sec,1)

    # Copy original body: paragraphs 14 onward, including original table.
    body_start=src.Paragraphs(14).Range.Start
    body=src.Range(body_start,src.Content.End)
    insert=doc.Content.Characters.Last.Duplicate; insert.Collapse(wdCollapseEnd)
    insert.FormattedText=body.FormattedText

    # Base body style and heading hierarchy.
    caption_style(doc)
    h1s=["CHƯƠNG 1.","CHƯƠNG 2."]
    h2s=["2.1. Thời điểm du lịch lý tưởng","2.2. Phương tiện","2.3. Địa điểm thăm quan"]
    h3s=["2.2.1. Phương tiện đến Chiang Mai","2.2.2. Các phương tiện di chuyển tại Chiang Mai"]
    for p in doc.Paragraphs:
        t=text(p).strip()
        if not t: continue
        if t.startswith("CHƯƠNG 1.") or t.startswith("CHƯƠNG 2."):
            p.Style="Heading 1"; p.Alignment=wdAlignLeft
        elif any(t.startswith(x) for x in h3s):
            p.Style="Heading 3"; p.Alignment=wdAlignLeft
        elif any(t.startswith(x) for x in h2s):
            p.Style="Heading 2"; p.Alignment=wdAlignLeft
        elif t.startswith("- "):
            try: p.Style="Style Trừ"
            except: pass
        elif t.startswith("+ "):
            try: p.Style="Style Cộng"
            except: pass
        elif t not in ["MỤC LỤC","DANH MỤC MINH HỌA","BỘ GIÁO DỤC VÀ ĐÀO TẠO","TRƯỜNG ĐẠI HỌC THĂNG LONG",
                       "TIỂU LUẬN","CHIANG MAI ĐÓA HỒNG PHƯƠNG BẮC XỨ CHÙA VÀNG","HÀ NỘI - 2026"]:
            try: p.Style="DoanVB"
            except: pass

    # Add footnote at Lanna.
    p=findp(doc,"Chiang Mai được mệnh danh")
    rr=p.Range.Duplicate; pos=text(p).find("Lanna")
    doc.Footnotes.Add(doc.Range(p.Range.Start+pos+5,p.Range.Start+pos+5),
                      Text="Một quốc gia cổ đại tồn tại từ TK 13 đến cuối TK 18")

    # Insert supplied reference photo after paragraph 2 of chapter 1.
    p=findp(doc,"Từng là thủ đô của một vương quốc hùng mạnh")
    rr=p.Range.Duplicate; rr.Collapse(wdCollapseEnd); rr.InsertParagraphAfter(); rr.Collapse(wdCollapseEnd)
    pic=rr.InlineShapes.AddPicture(FileName=str(IMG),LinkToFile=False,SaveWithDocument=True)
    pic.LockAspectRatio=True; pic.Width=360
    pic.Range.ParagraphFormat.Alignment=wdAlignCenter
    try:
        sh=pic.ConvertToShape()
        sh.WrapFormat.Type=3
        sh.Shadow.Visible=True; sh.Shadow.Blur=4; sh.Shadow.OffsetX=2; sh.Shadow.OffsetY=2
        sh.ConvertToInlineShape()
    except: pass
    # Locate last inline picture (the inserted photo, not the logo).
    pic=doc.InlineShapes(doc.InlineShapes.Count)
    caplabel(doc,"Ảnh")
    pic.Range.InsertCaption(Label="Ảnh",Title=" Chiang Mai mùa hoa nở",Position=wdCaptionPositionBelow,ExcludeLabel=False)

    # Landscape section begins immediately before the existing table.
    table=doc.Tables(1)
    rr=table.Range.Duplicate; rr.Collapse(wdCollapseStart); rr.InsertBreak(wdSectionBreakNextPage)
    land_sec=table.Range.Sections(1); set_a4(land_sec,True)
    add_page_number(land_sec,3)

    # Table caption and formatting.
    caplabel(doc,"Bảng")
    table.Range.Select()
    word.Selection.InsertCaption(Label="Bảng",Title=" Những điểm thăm quan nổi tiếng",Position=wdCaptionPositionAbove,ExcludeLabel=False)
    table.Range.Font.Name="Times New Roman"; table.Range.Font.Size=13
    table.Rows.AllowBreakAcrossPages=True
    table.AllowAutoFit=False
    table.Columns(1).Width=155; table.Columns(2).Width=420
    for c in table.Rows(1).Cells:
        c.Range.Font.Bold=True
        c.Range.ParagraphFormat.Alignment=wdAlignCenter
        c.VerticalAlignment=1
        c.Shading.BackgroundPatternColor=0xD9EAD3
    for row in table.Rows:
        for c in row.Cells:
            c.VerticalAlignment=1
            c.Range.ParagraphFormat.SpaceBefore=0
            c.Range.ParagraphFormat.SpaceAfter=0
            c.Range.ParagraphFormat.LineSpacing=1.0
            if row.Index>1: c.Range.ParagraphFormat.Alignment=wdAlignJustify

    # Page numbering and fields.
    for i in range(1,doc.Sections.Count):
        if i!=2:
            clear_footer(doc.Sections(i))
    add_page_number(doc.Sections(2),1)
    add_page_number(doc.Sections(3),3)
    doc.Fields.Update()
    for x in doc.TablesOfContents:
        try: x.Update()
        except: pass
    for x in doc.TablesOfFigures:
        try: x.Update()
        except: pass
    word.ActiveDocument.Repaginate()
    doc.Save()
    doc.ExportAsFixedFormat(str(PDF),17)
    print("OUTPUT",OUT)
    print("PDF",PDF)
    print("SECTIONS",doc.Sections.Count,"TABLES",doc.Tables.Count,"IMAGES",doc.InlineShapes.Count,"FOOTNOTES",doc.Footnotes.Count)
finally:
    try:
        if doc: doc.Close(SaveChanges=True)
    except: pass
    try:
        if src: src.Close(SaveChanges=False)
    except: pass
    try: word.Quit()
    except: pass
