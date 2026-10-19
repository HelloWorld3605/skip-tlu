from pathlib import Path
import win32com.client as win32

ROOT=Path(r"D:\LearningPesonal\Project\skiptlu")
WEEK=ROOT/"artifacts"/"week4"
OUT=WEEK/"generated"/"A57649_NguyenDangPhuongNhi_LuyenTap_BaiSo1.docx"
PDF=WEEK/"generated"/"A57649_NguyenDangPhuongNhi_LuyenTap_BaiSo1.pdf"

wdAlignCenter=1; wdCaptionPositionAbove=0; wdCaptionPositionBelow=1
wdFieldPage=33

def txt(p): return p.Range.Text.replace("\r","").replace("\x07","")

def findp(doc,needle):
    for p in doc.Paragraphs:
        if needle in txt(p): return p
    raise RuntimeError(needle)

def label(doc,name):
    try: x=doc.Application.CaptionLabels(name)
    except: x=doc.Application.CaptionLabels.Add(name)
    x.IncludeChapterNumber=True; x.ChapterStyleLevel=1; x.NumberStyle=0; x.Separator=1

word=win32.DispatchEx("Word.Application"); word.Visible=False; word.DisplayAlerts=0
doc=word.Documents.Open(str(OUT),ReadOnly=False)
try:
    # Remove explicit heading numbers and apply real multilevel list template 2.
    heading_info=[
        ("CHƯƠNG 1.\tGIỚI THIỆU VỀ CHIANG MAI", "GIỚI THIỆU VỀ CHIANG MAI",1),
        ("CHƯƠNG 2.\tCẨM NANG DU LỊCH CHIANG MAI", "CẨM NANG DU LỊCH CHIANG MAI",1),
        ("2.1. Thời điểm du lịch lý tưởng","Thời điểm du lịch lý tưởng",2),
        ("2.2. Phương tiện","Phương tiện",2),
        ("2.2.1. Phương tiện đến Chiang Mai","Phương tiện đến Chiang Mai",3),
        ("2.2.2. Các phương tiện di chuyển tại Chiang Mai","Các phương tiện di chuyển tại Chiang Mai",3),
        ("2.3. Địa điểm thăm quan","Địa điểm thăm quan",2),
    ]
    for old,new,level in heading_info:
        p=findp(doc,old); p.Range.Text=new+"\r"; p.Style=f"Heading {level}"
    # Apply the exact built-in outline template whose formats are 1., 1.1., 1.1.1.
    headings=[p for p in doc.Paragraphs if str(p.Style) in ["Heading 1","Heading 2","Heading 3"] and txt(p).strip() in
              ["GIỚI THIỆU VỀ CHIANG MAI","CẨM NANG DU LỊCH CHIANG MAI","Thời điểm du lịch lý tưởng","Phương tiện",
               "Phương tiện đến Chiang Mai","Các phương tiện di chuyển tại Chiang Mai","Địa điểm thăm quan"]]
    if headings:
        start=headings[0].Range.Start; end=headings[-1].Range.End
        rng=doc.Range(start,end)
        template=word.ListGalleries(3).ListTemplates(2)
        rng.ListFormat.ApplyListTemplate(template, True, 2)
        for p in headings:
            t=txt(p).strip()
            level=1 if t in ["GIỚI THIỆU VỀ CHIANG MAI","CẨM NANG DU LỊCH CHIANG MAI"] else (3 if t in ["Phương tiện đến Chiang Mai","Các phương tiện di chuyển tại Chiang Mai"] else 2)
            p.Range.ListFormat.ListLevelNumber=level

    # Automatic captions.
    label(doc,"Ảnh"); label(doc,"Bảng")
    # Remove the typed image caption and insert a real Word caption.
    for needle in ["Ảnh 1.1. Chiang Mai mùa hoa nở","Bảng 2.1. Những điểm thăm quan nổi tiếng"]:
        try:
            p=findp(doc,needle); p.Range.Delete()
        except: pass
    # image is second inline shape (first is logo)
    pic=doc.InlineShapes(2)
    pic.Range.InsertCaption(Label="Ảnh",Title=" Chiang Mai mùa hoa nở",Position=wdCaptionPositionBelow,ExcludeLabel=False)
    table=doc.Tables(1)
    table.Range.Select()
    word.Selection.InsertCaption(Label="Bảng",Title=" Những điểm thăm quan nổi tiếng",Position=wdCaptionPositionAbove,ExcludeLabel=False)

    # Caption style.
    try: cap=doc.Styles("Caption")
    except: cap=doc.Styles.Add("Caption")
    cap.Font.Name="Times New Roman"; cap.Font.Size=13; cap.Font.Italic=True
    cap.ParagraphFormat.Alignment=wdAlignCenter; cap.ParagraphFormat.SpaceBefore=6; cap.ParagraphFormat.SpaceAfter=6

    # Footnote.
    p=findp(doc,"Chiang Mai được mệnh danh")
    if doc.Footnotes.Count==0:
        pos=txt(p).find("Lanna")
        doc.Footnotes.Add(doc.Range(p.Range.Start+pos+5,p.Range.Start+pos+5),Text="Một quốc gia cổ đại tồn tại từ TK 13 đến cuối TK 18")

    # Page numbers: sections 4 and 5 only.
    for sec in doc.Sections:
        for i in (1,2,3):
            try:
                sec.Headers(i).LinkToPrevious=False; sec.Footers(i).LinkToPrevious=False
            except: pass
        try: sec.Footers(1).Range.Text=""
        except: pass
    for idx,start in [(4,1),(5,3)]:
        sec=doc.Sections(idx)
        f=sec.Footers(1); f.Range.Text=""; f.Range.ParagraphFormat.Alignment=wdAlignCenter
        f.Range.Fields.Add(f.Range,wdFieldPage)
        f.PageNumbers.RestartNumberingAtSection=True; f.PageNumbers.StartingNumber=start

    # Update TOC/illustration lists and page fields.
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
    doc.Save()
    doc.ExportAsFixedFormat(str(PDF),17)
    print("FINAL",OUT)
    print("PDF",PDF)
    print("sections",doc.Sections.Count,"tables",doc.Tables.Count,"images",doc.InlineShapes.Count,"footnotes",doc.Footnotes.Count)
finally:
    doc.Close(SaveChanges=True); word.Quit()
