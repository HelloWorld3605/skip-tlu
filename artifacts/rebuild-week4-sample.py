import os, re, time
from pathlib import Path
import win32com.client as win32

ROOT=Path(r"D:\LearningPesonal\Project\skiptlu")
WEEK=ROOT/"artifacts"/"week4"
SRC=next(WEEK.glob("BaiLam_LuyenTap_BaiSo1.docx"))
IMG=WEEK/"Picture_De1.jpg"
OUT=WEEK/"generated"/"A57649_NguyenDangPhuongNhi_LuyenTap_BaiSo1.docx"
PDF=WEEK/"generated"/"A57649_NguyenDangPhuongNhi_LuyenTap_BaiSo1.pdf"
OUT.parent.mkdir(exist_ok=True)

wdCollapseStart=1; wdCollapseEnd=0
wdSectionBreakNextPage=2
wdAlignCenter=1; wdAlignLeft=0; wdAlignJustify=3
wdOrientPortrait=0; wdOrientLandscape=1
wdHeaderFooterPrimary=1
wdCaptionPositionAbove=0; wdCaptionPositionBelow=1
wdLineSpaceMultiple=5
wdFieldTOC=13
wdPageNumberStyleArabic=0

def para_by_text(doc, text):
    for p in doc.Paragraphs:
        if text in p.Range.Text.replace("\r","").replace("\x07",""):
            return p
    raise ValueError(f"paragraph not found: {text}")

def clear_para(p):
    p.Range.Text = ""

def set_font(rng, size=13, bold=False, italic=False, name="Times New Roman"):
    rng.Font.Name=name
    rng.Font.NameAscii=name
    rng.Font.Size=size
    rng.Font.Bold=bold
    rng.Font.Italic=italic

def set_page(sec, landscape=False):
    ps=sec.PageSetup
    ps.Orientation=wdOrientLandscape if landscape else wdOrientPortrait
    if landscape:
        ps.PageWidth=win32.constants.wdPaperA4 and 841.89
        ps.PageHeight=595.28
    else:
        ps.PageWidth=595.28
        ps.PageHeight=841.89
    ps.TopMargin=56.7
    ps.BottomMargin=56.7
    ps.LeftMargin=85.05
    ps.RightMargin=42.52
    ps.HeaderDistance=28.35
    ps.FooterDistance=28.35

def unlink(sec):
    try:
        sec.Headers(wdHeaderFooterPrimary).LinkToPrevious=False
        sec.Footers(wdHeaderFooterPrimary).LinkToPrevious=False
    except Exception:
        pass

def remove_page_numbers(sec):
    try:
        sec.Footers(wdHeaderFooterPrimary).Range.Fields.Unlink()
        sec.Footers(wdHeaderFooterPrimary).Range.Text=""
    except Exception:
        pass

def add_page_number(sec, start=1):
    unlink(sec)
    f=sec.Footers(wdHeaderFooterPrimary)
    r=f.Range
    r.Text=""
    r.ParagraphFormat.Alignment=wdAlignCenter
    fld=r.Fields.Add(r, 33)
    try:
        sec.Footers(wdHeaderFooterPrimary).PageNumbers.RestartNumberingAtSection=True
        sec.Footers(wdHeaderFooterPrimary).PageNumbers.StartingNumber=start
    except Exception:
        pass

def style_caption(doc):
    try:
        s=doc.Styles("Caption")
    except Exception:
        s=doc.Styles.Add("Caption")
    s.Font.Name="Times New Roman"; s.Font.NameAscii="Times New Roman"; s.Font.Size=13
    s.Font.Italic=True; s.Font.ColorIndex=0
    s.ParagraphFormat.Alignment=wdAlignCenter
    s.ParagraphFormat.SpaceBefore=6
    s.ParagraphFormat.SpaceAfter=6
    s.ParagraphFormat.LineSpacingRule=wdLineSpaceMultiple
    s.ParagraphFormat.LineSpacing=1.3

def configure_caption_label(doc, label):
    labels=doc.Application.CaptionLabels
    try:
        item=labels(label)
    except Exception:
        item=labels.Add(label)
    item.IncludeChapterNumber=True
    item.ChapterStyleLevel=1
    item.NumberStyle=0
    item.Separator=1
    return item

word=win32.DispatchEx("Word.Application")
word.Visible=False
word.DisplayAlerts=0
try:
    doc=word.Documents.Open(str(SRC), ReadOnly=False)
    # Save a clean working copy first.
    doc.SaveAs2(str(OUT), FileFormat=16)

    # ----- Page setup / base styles -----
    for sec in doc.Sections:
        set_page(sec, False)
        unlink(sec)
        remove_page_numbers(sec)
    style_caption(doc)
    for nm in ["Normal","Heading 1","Heading 2","Heading 3","DoanVB","Style Trừ","Style Cộng"]:
        try:
            st=doc.Styles(nm)
            st.Font.Name="Times New Roman"; st.Font.NameAscii="Times New Roman"
        except Exception:
            pass

    # ----- Cover -----
    replacements={
        "HỌ TÊN CỦA SINH VIÊN":"NGUYỄN ĐẶNG PHƯƠNG NHI",
        "MÃ CỦA SINH VIÊN":"A57649",
        "NGÀNH CỦA SINH VIÊN":"KẾ TOÁN",
    }
    for old,new in replacements.items():
        rng=doc.Content
        find=rng.Find
        find.Text=old
        find.Replacement.Text=new
        find.Execute(Replace=2)

    for text in ["BỘ GIÁO DỤC VÀ ĐÀO TẠO","TRƯỜNG ĐẠI HỌC THĂNG LONG","TIỂU LUẬN",
                 "CHIANG MAI ĐÓA HỒNG PHƯƠNG BẮC XỨ CHÙA VÀNG",
                 "SINH VIÊN THỰC HIỆN: NGUYỄN ĐẶNG PHƯƠNG NHI",
                 "MÃ SINH VIÊN: A57649","NGÀNH: KẾ TOÁN","HÀ NỘI - 2026"]:
        p=para_by_text(doc,text)
        p.Alignment=wdAlignCenter
        p.Range.Font.Name="Times New Roman"; p.Range.Font.NameAscii="Times New Roman"
    p=para_by_text(doc,"BỘ GIÁO DỤC VÀ ĐÀO TẠO"); set_font(p.Range,13,False)
    p=para_by_text(doc,"TRƯỜNG ĐẠI HỌC THĂNG LONG"); set_font(p.Range,13,True)
    p=para_by_text(doc,"TIỂU LUẬN"); set_font(p.Range,20,True)
    p=para_by_text(doc,"CHIANG MAI ĐÓA HỒNG PHƯƠNG BẮC XỨ CHÙA VÀNG"); set_font(p.Range,17,True)
    for text in ["SINH VIÊN THỰC HIỆN: NGUYỄN ĐẶNG PHƯƠNG NHI","MÃ SINH VIÊN: A57649","NGÀNH: KẾ TOÁN"]:
        p=para_by_text(doc,text)
        set_font(p.Range,13,True)
        p.Range.ParagraphFormat.TabStops.ClearAll()
        p.Range.ParagraphFormat.TabStops.Add(283.5)
        p.Range.Text=p.Range.Text.replace(": ",":\t")
    p=para_by_text(doc,"HÀ NỘI - 2026"); set_font(p.Range,13,True)
    # logo is the existing inline image in the cover
    if doc.InlineShapes.Count:
        logo=doc.InlineShapes(1)
        logo.Range.ParagraphFormat.Alignment=wdAlignCenter
        logo.Width=58; logo.Height=58
    # cover spacing approximates the provided sample
    for text,after in [
        ("BỘ GIÁO DỤC VÀ ĐÀO TẠO",2),("TRƯỜNG ĐẠI HỌC THĂNG LONG",6),
        ("TIỂU LUẬN",18),("CHIANG MAI ĐÓA HỒNG PHƯƠNG BẮC XỨ CHÙA VÀNG",70),
        ("NGÀNH:",4),("HÀ NỘI - 2026",0)]:
        p=para_by_text(doc,text); p.Range.ParagraphFormat.SpaceAfter=after
    # border line under university name
    p=para_by_text(doc,"TRƯỜNG ĐẠI HỌC THĂNG LONG")
    try:
        p.Borders(3).LineStyle=1
        p.Borders(3).LineWidth=4
    except Exception:
        pass

    # ----- Split front matter into 3 pages/sections -----
    cover_end=para_by_text(doc,"HÀ NỘI - 2026").Range.Duplicate
    cover_end.Collapse(wdCollapseEnd); cover_end.InsertBreak(wdSectionBreakNextPage)

    toc=para_by_text(doc,"MỤC LỤC")
    # remove following placeholder paragraph
    try:
        nxt=toc.Range.Next()
        nxt.Text=""
    except Exception: pass
    toc.Alignment=wdAlignCenter; set_font(toc.Range,13,True)
    toc.Range.ParagraphFormat.SpaceAfter=12
    # insert TOC in the paragraph immediately after heading
    r=toc.Range.Duplicate; r.Collapse(wdCollapseEnd); r.InsertParagraphAfter()
    toc_field_range=toc.Range.Next()
    doc.TablesOfContents.Add(Range=toc_field_range, RightAlignPageNumbers=True, UseHeadingStyles=True,
                             UpperHeadingLevel=1, LowerHeadingLevel=3, IncludePageNumbers=True,
                             UseHyperlinks=True, HidePageNumbersInWeb=True)

    # find TOC end and split
    toc_end=para_by_text(doc,"MỤC LỤC").Range.Duplicate
    # move to section 2's end safely
    sec2=doc.Sections(2)
    sec2_end=sec2.Range.Duplicate; sec2_end.Collapse(wdCollapseEnd); sec2_end.InsertBreak(wdSectionBreakNextPage)

    ill=para_by_text(doc,"DANH MỤC MINH HỌA")
    ill.Alignment=wdAlignCenter; set_font(ill.Range,13,True)
    ill.Range.ParagraphFormat.SpaceAfter=12
    # Clear the placeholder paragraph and insert the two real illustration lists.
    try: ill.Range.Next().Text=""
    except Exception: pass
    rr=ill.Range.Duplicate; rr.Collapse(wdCollapseEnd); rr.InsertParagraphAfter()
    list_range=ill.Range.Next()
    configure_caption_label(doc,"Ảnh"); configure_caption_label(doc,"Bảng")
    doc.TablesOfFigures.Add(Range=list_range, Caption="Ảnh", IncludeLabel=True, RightAlignPageNumbers=True, UseHyperlinks=True)
    list_range.End=doc.TablesOfFigures(1).Range.End
    list_range.InsertParagraphAfter()
    list2=doc.Range(list_range.End+1,list_range.End+1)
    doc.TablesOfFigures.Add(Range=list2, Caption="Bảng", IncludeLabel=True, RightAlignPageNumbers=True, UseHyperlinks=True)

    sec3=doc.Sections(3)
    sec3_end=sec3.Range.Duplicate; sec3_end.Collapse(wdCollapseEnd); sec3_end.InsertBreak(wdSectionBreakNextPage)

    # ----- Content formatting -----
    heading1=[
        "CHƯƠNG 1.\tGIỚI THIỆU VỀ CHIANG MAI",
        "CHƯƠNG 2.\tCẨM NANG DU LỊCH CHIANG MAI",
    ]
    heading2=["2.1. Thời điểm du lịch lý tưởng","2.2. Phương tiện","2.3. Địa điểm thăm quan"]
    heading3=["2.2.1. Phương tiện đến Chiang Mai","2.2.2. Các phương tiện di chuyển tại Chiang Mai"]
    for text in heading1:
        p=para_by_text(doc,text); p.Range.Text=p.Range.Text.replace("\t","    ").replace("\r","")
        p.Style="Heading 1"; p.Alignment=wdAlignLeft
    for text in heading2:
        p=para_by_text(doc,text); p.Style="Heading 2"; p.Alignment=wdAlignLeft
    for text in heading3:
        p=para_by_text(doc,text); p.Style="Heading 3"; p.Alignment=wdAlignLeft

    # Body/list styles
    for p in doc.Paragraphs:
        t=p.Range.Text.replace("\r","").strip()
        if not t: continue
        if t in heading1 or t in heading2 or t in heading3: continue
        if t.startswith("- "):
            if "Vietjet" in t or "Airasia" in t or "Bangkok Airway" in t or "Thai AirAsia" in t:
                p.Style="Style Trừ"
            else:
                p.Style="Style Trừ"
        elif t.startswith("+ "):
            p.Style="Style Cộng"
        elif t not in ["MỤC LỤC","DANH MỤC MINH HỌA"]:
            try: p.Style="DoanVB"
            except Exception: pass

    # Make the four airport items and four transport items true dash lists while retaining sample appearance.
    for t in ["- Vietjet Air;","- Airasia;","- Bangkok Airway;","- Thai AirAsia... ",
              "- Xe Song Taew;","- Xe Tuk Tuk;","- Taxi;","- Xe máy."]:
        try:
            p=para_by_text(doc,t)
            p.Range.ParagraphFormat.LeftIndent=28.35
            p.Range.ParagraphFormat.FirstLineIndent=-14.17
        except Exception: pass

    # Insert the required footnote after Lanna.
    lp=para_by_text(doc,"Chiang Mai được mệnh danh")
    rr=lp.Range.Duplicate
    pos=rr.Text.find("Lanna")
    if pos>=0:
        r=doc.Range(lp.Range.Start+pos+5,lp.Range.Start+pos+5)
        doc.Footnotes.Add(r, Text="Một quốc gia cổ đại tồn tại từ TK 13 đến cuối TK 18")

    # Insert the reference image after the second body paragraph of chapter 1.
    target=para_by_text(doc,"Từng là thủ đô của một vương quốc hùng mạnh")
    r=target.Range.Duplicate; r.Collapse(wdCollapseEnd); r.InsertParagraphAfter(); r.Collapse(wdCollapseEnd)
    pic=r.InlineShapes.AddPicture(FileName=str(IMG), LinkToFile=False, SaveWithDocument=True)
    pic.LockAspectRatio=True
    pic.Width=360
    pic.Range.ParagraphFormat.Alignment=wdAlignCenter
    # rounded/shadow style approximation using a Shape conversion
    try:
        sh=pic.ConvertToShape()
        sh.WrapFormat.Type=3
        sh.Fill.Transparency=0
        sh.Line.Weight=1
        sh.Shadow.Visible=True
        sh.Shadow.Blur=4
        sh.Shadow.OffsetX=2
        sh.Shadow.OffsetY=2
        sh.ConvertToInlineShape()
    except Exception:
        pass

    # Image caption: automatic numbering with chapter.
    configure_caption_label(doc,"Ảnh")
    try:
        pic2=doc.InlineShapes(doc.InlineShapes.Count)
        pic2.Range.InsertCaption(Label="Ảnh", Title=" Chiang Mai mùa hoa nở", Position=wdCaptionPositionBelow, ExcludeLabel=False)
    except Exception:
        # fallback: explicit field-based caption
        pass

    # ----- Landscape section starting at the table -----
    table=doc.Tables(1)
    start=table.Range.Duplicate; start.Collapse(wdCollapseStart)
    start.InsertBreak(wdSectionBreakNextPage)
    # The new section is the one containing the table.
    table_section=table.Range.Sections(1)
    set_page(table_section, True)
    unlink(table_section)

    # table caption above
    configure_caption_label(doc,"Bảng")
    table.Range.Select()
    sel=word.Selection
    sel.InsertCaption(Label="Bảng", Title=" Những điểm thăm quan nổi tiếng", Position=wdCaptionPositionAbove, ExcludeLabel=False)

    # table formatting
    table.AutoFitBehavior(1)
    table.AllowAutoFit=False
    table.Range.Font.Name="Times New Roman"; table.Range.Font.NameAscii="Times New Roman"; table.Range.Font.Size=13
    table.Rows.AllowBreakAcrossPages=True
    # widths matching sample
    table.Columns(1).Width=155
    table.Columns(2).Width=420
    # header
    for c in table.Rows(1).Cells:
        c.Range.Font.Bold=True
        c.Range.ParagraphFormat.Alignment=wdAlignCenter
        c.Shading.BackgroundPatternColor=0xD9EAD3
    for row in table.Rows:
        for c in row.Cells:
            c.VerticalAlignment=1
            c.Range.ParagraphFormat.Alignment=wdAlignJustify
            c.Range.ParagraphFormat.SpaceBefore=0
            c.Range.ParagraphFormat.SpaceAfter=0
            c.Range.ParagraphFormat.LineSpacing=1.0
    # sample header is light peach
    for c in table.Rows(1).Cells:
        c.Shading.BackgroundPatternColor=0xD9EAD3
    # final paragraph after table remains in landscape section.

    # ----- Page numbers -----
    for sec in doc.Sections:
        unlink(sec)
        remove_page_numbers(sec)
    # content starts at section 4; table landscape section continues numbering.
    for sec in doc.Sections[3:]:
        add_page_number(sec,1 if sec.Index==4 else 3)

    # Fields / pagination
    doc.Fields.Update()
    for toc_obj in doc.TablesOfContents:
        try: toc_obj.Update()
        except Exception: pass
    for tof in doc.TablesOfFigures:
        try: tof.Update()
        except Exception: pass
    word.ActiveDocument.Repaginate()

    doc.Save()
    # PDF preview
    doc.ExportAsFixedFormat(str(PDF), 17)
    print("OUTPUT", OUT)
    print("PDF", PDF)
    print("SECTIONS", doc.Sections.Count)
    print("TABLES", doc.Tables.Count, "INLINE_SHAPES", doc.InlineShapes.Count, "FOOTNOTES", doc.Footnotes.Count)
    print("PARAS", doc.Paragraphs.Count)
finally:
    try: doc.Close(SaveChanges=True)
    except Exception: pass
    try: word.Quit()
    except Exception: pass
