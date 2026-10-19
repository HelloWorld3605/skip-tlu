from pathlib import Path
import win32com.client as win32

ROOT=Path(r"D:\LearningPesonal\Project\skiptlu")
WEEK=ROOT/"artifacts"/"week4"
SRC=next(WEEK.glob("BaiLam_LuyenTap_BaiSo1.docx"))
IMG=WEEK/"Picture_De1.jpg"
OUT=WEEK/"generated"/"A57649_NguyenDangPhuongNhi_LuyenTap_BaiSo1.docx"
PDF=WEEK/"generated"/"A57649_NguyenDangPhuongNhi_LuyenTap_BaiSo1.pdf"
OUT.parent.mkdir(exist_ok=True)

wdCollapseEnd=0; wdPageBreak=7; wdSectionBreakNextPage=2
wdAlignCenter=1; wdAlignLeft=0; wdAlignJustify=3
wdOrientPortrait=0; wdOrientLandscape=1
wdCaptionPositionAbove=0; wdCaptionPositionBelow=1
wdFieldTOC=13; wdFieldPage=33

def ptext(p): return p.Range.Text.replace("\r","").replace("\x07","")

def findp(doc, needle):
    for p in doc.Paragraphs:
        if needle in ptext(p):
            return p
    raise RuntimeError("missing "+needle)

def set_a4(sec, landscape=False):
    ps=sec.PageSetup
    ps.Orientation=wdOrientLandscape if landscape else wdOrientPortrait
    ps.PageWidth=841.89 if landscape else 595.28
    ps.PageHeight=595.28 if landscape else 841.89
    ps.TopMargin=56.7; ps.BottomMargin=56.7; ps.LeftMargin=85.05; ps.RightMargin=42.52
    ps.HeaderDistance=28.35; ps.FooterDistance=28.35

def unlink(sec):
    for i in (1,2,3):
        try:
            sec.Headers(i).LinkToPrevious=False
            sec.Footers(i).LinkToPrevious=False
        except: pass

def footer_clear(sec):
    unlink(sec)
    try: sec.Footers(1).Range.Text=""
    except: pass

def footer_page(sec,start):
    unlink(sec)
    f=sec.Footers(1); f.Range.Text=""; f.Range.ParagraphFormat.Alignment=wdAlignCenter
    f.Range.Fields.Add(f.Range,wdFieldPage)
    f.PageNumbers.RestartNumberingAtSection=True
    f.PageNumbers.StartingNumber=start

def caplabel(doc,name):
    try: x=doc.Application.CaptionLabels(name)
    except: x=doc.Application.CaptionLabels.Add(name)
    x.IncludeChapterNumber=True; x.ChapterStyleLevel=1; x.NumberStyle=0; x.Separator=1

def caption_style(doc):
    try: s=doc.Styles("Caption")
    except: s=doc.Styles.Add("Caption")
    s.Font.Name="Times New Roman"; s.Font.NameAscii="Times New Roman"; s.Font.Size=13; s.Font.Italic=True
    s.ParagraphFormat.Alignment=wdAlignCenter; s.ParagraphFormat.SpaceBefore=6; s.ParagraphFormat.SpaceAfter=6

word=win32.DispatchEx("Word.Application"); word.Visible=False; word.DisplayAlerts=0
src=None; doc=None
try:
    src=word.Documents.Open(str(SRC),ReadOnly=True)
    doc=word.Documents.Add()
    set_a4(doc.Sections(1),False)
    sel=word.Selection

    # Cover from original, preserving logo.
    sel.Range.FormattedText=src.Range(0,src.Paragraphs(9).Range.End).FormattedText
    for a,b in {
        "HỌ TÊN CỦA SINH VIÊN":"NGUYỄN ĐẶNG PHƯƠNG NHI",
        "MÃ CỦA SINH VIÊN":"A57649",
        "NGÀNH CỦA SINH VIÊN":"KẾ TOÁN",
    }.items():
        r=doc.Content.Duplicate; f=r.Find; f.Text=a; f.Replacement.Text=b; f.Execute(Replace=2)
    for needle,size,bold in [
        ("BỘ GIÁO DỤC",13,False),("TRƯỜNG ĐẠI HỌC",13,True),("TIỂU LUẬN",20,True),
        ("CHIANG MAI ĐÓA HỒNG",17,True),("SINH VIÊN THỰC HIỆN:",13,True),
        ("MÃ SINH VIÊN:",13,True),("NGÀNH:",13,True),("HÀ NỘI - 2026",13,True)]:
        p=findp(doc,needle); p.Alignment=wdAlignCenter; p.Range.Font.Name="Times New Roman"; p.Range.Font.Size=size; p.Range.Font.Bold=bold
    for needle in ["SINH VIÊN THỰC HIỆN:","MÃ SINH VIÊN:","NGÀNH:"]:
        p=findp(doc,needle); s=ptext(p).strip(); label,value=s.split(":",1)
        p.Range.Text=label.upper()+":\t"+value.strip().upper()+"\r"
        p.Alignment=wdAlignCenter; p.Range.Font.Name="Times New Roman"; p.Range.Font.Size=13; p.Range.Font.Bold=True
        p.Range.ParagraphFormat.TabStops.ClearAll(); p.Range.ParagraphFormat.TabStops.Add(283.5)
    if doc.InlineShapes.Count:
        logo=doc.InlineShapes(1); logo.Width=58; logo.Height=58; logo.Range.ParagraphFormat.Alignment=wdAlignCenter
    footer_clear(doc.Sections(1))

    # TOC page.
    sel.EndKey(Unit=6); sel.InsertBreak(wdPageBreak); sel.TypeText("MỤC LỤC"); sel.ParagraphFormat.Alignment=wdAlignCenter
    sel.Font.Name="Times New Roman"; sel.Font.Size=13; sel.Bold=True; sel.InsertParagraphAfter(); sel.Collapse(wdCollapseEnd)
    sel.Fields.Add(sel.Range,wdFieldTOC,'\\o "1-3" \\h \\z \\u',True)
    sel.InsertParagraphAfter()

    # Illustration list page.
    sel.EndKey(Unit=6); sel.InsertBreak(wdPageBreak); sel.TypeText("DANH MỤC MINH HỌA"); sel.ParagraphFormat.Alignment=wdAlignCenter
    sel.Font.Name="Times New Roman"; sel.Font.Size=13; sel.Bold=True; sel.InsertParagraphAfter(); sel.Collapse(wdCollapseEnd)
    sel.Fields.Add(sel.Range,wdFieldTOC,'\\h \\z \\c "Ảnh"',True); sel.InsertParagraphAfter(); sel.Collapse(wdCollapseEnd)
    sel.Fields.Add(sel.Range,wdFieldTOC,'\\h \\z \\c "Bảng"',True); sel.InsertParagraphAfter()

    # Content section starts page 1.
    sel.EndKey(Unit=6); sel.InsertBreak(wdSectionBreakNextPage)
    content_sec=doc.Sections(doc.Sections.Count); set_a4(content_sec,False); footer_page(content_sec,1)

    # Copy body as formatted content into a fresh paragraph.
    body=src.Range(src.Paragraphs(14).Range.Start,src.Content.End)
    sel.EndKey(Unit=6); sel.InsertParagraphAfter(); sel.Collapse(wdCollapseEnd)
    sel.Range.FormattedText=body.FormattedText

    caption_style(doc)
    # Headings / body styles.
    for p in doc.Paragraphs:
        t=ptext(p).strip()
        if not t: continue
        if t.startswith("CHƯƠNG 1.") or t.startswith("CHƯƠNG 2."): p.Style="Heading 1"
        elif t.startswith("2.1.") or t.startswith("2.2.") or t.startswith("2.3."): p.Style="Heading 2"
        elif t.startswith("2.2.1.") or t.startswith("2.2.2."): p.Style="Heading 3"
        elif t.startswith("- "):
            try: p.Style="Style Trừ"
            except: pass
        elif t.startswith("+ "):
            try: p.Style="Style Cộng"
            except: pass
        elif t not in ["MỤC LỤC","DANH MỤC MINH HỌA"]:
            try: p.Style="DoanVB"
            except: pass

    # Footnote.
    p=findp(doc,"Chiang Mai được mệnh danh"); pos=ptext(p).find("Lanna")
    doc.Footnotes.Add(doc.Range(p.Range.Start+pos+5,p.Range.Start+pos+5),Text="Một quốc gia cổ đại tồn tại từ TK 13 đến cuối TK 18")

    # Reference photo.
    p=findp(doc,"Từng là thủ đô của một vương quốc hùng mạnh")
    rr=p.Range.Duplicate; rr.Collapse(wdCollapseEnd); rr.InsertParagraphAfter(); rr.Collapse(wdCollapseEnd)
    pic=rr.InlineShapes.AddPicture(FileName=str(IMG),LinkToFile=False,SaveWithDocument=True); pic.LockAspectRatio=True; pic.Width=360
    pic.Range.ParagraphFormat.Alignment=wdAlignCenter
    try:
        sh=pic.ConvertToShape(); sh.WrapFormat.Type=3; sh.Shadow.Visible=True; sh.Shadow.Blur=4; sh.Shadow.OffsetX=2; sh.Shadow.OffsetY=2; pic=sh.ConvertToInlineShape()
    except: pass
    caplabel(doc,"Ảnh"); pic.Range.InsertCaption(Label="Ảnh",Title=" Chiang Mai mùa hoa nở",Position=wdCaptionPositionBelow,ExcludeLabel=False)

    # Landscape section before table.
    table=doc.Tables(1); rr=table.Range.Duplicate; rr.Collapse(1); rr.InsertBreak(wdSectionBreakNextPage)
    land=table.Range.Sections(1); set_a4(land,True); footer_page(land,3)
    caplabel(doc,"Bảng"); table.Range.Select(); sel=word.Selection
    sel.InsertCaption(Label="Bảng",Title=" Những điểm thăm quan nổi tiếng",Position=wdCaptionPositionAbove,ExcludeLabel=False)
    table.Range.Font.Name="Times New Roman"; table.Range.Font.Size=13; table.AllowAutoFit=False
    table.Columns(1).Width=155; table.Columns(2).Width=420
    for c in table.Rows(1).Cells:
        c.Range.Font.Bold=True; c.Range.ParagraphFormat.Alignment=wdAlignCenter; c.VerticalAlignment=1; c.Shading.BackgroundPatternColor=0xD9EAD3
    for row in table.Rows:
        for c in row.Cells:
            c.VerticalAlignment=1; c.Range.ParagraphFormat.SpaceBefore=0; c.Range.ParagraphFormat.SpaceAfter=0; c.Range.ParagraphFormat.LineSpacing=1.0
            if row.Index>1: c.Range.ParagraphFormat.Alignment=wdAlignJustify

    # Final field updates.
    footer_clear(doc.Sections(1)); footer_page(doc.Sections(2),1); footer_page(doc.Sections(3),3)
    doc.Fields.Update()
    for x in doc.TablesOfContents:
        try: x.Update()
        except: pass
    for x in doc.TablesOfFigures:
        try: x.Update()
        except: pass
    word.ActiveDocument.Repaginate()
    doc.Save(); doc.ExportAsFixedFormat(str(PDF),17)
    print("OK",OUT); print("PDF",PDF); print("sections",doc.Sections.Count,"tables",doc.Tables.Count,"images",doc.InlineShapes.Count,"footnotes",doc.Footnotes.Count)
finally:
    try:
        if doc: doc.Close(SaveChanges=True)
    except: pass
    try:
        if src: src.Close(SaveChanges=False)
    except: pass
    try: word.Quit()
    except: pass
