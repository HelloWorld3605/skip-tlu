from pathlib import Path
from copy import deepcopy
from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_LINE_SPACING

ROOT=Path(r"D:\LearningPesonal\Project\skiptlu")
WEEK=ROOT/"artifacts"/"week4"
SRC=next(WEEK.glob("BaiLam_LuyenTap_BaiSo1.docx"))
LOGO=WEEK/"source-image.png"
PHOTO=WEEK/"Picture_De1.jpg"
OUT=WEEK/"generated"/"A57649_NguyenDangPhuongNhi_LuyenTap_BaiSo1.docx"
OUT.parent.mkdir(exist_ok=True)

src=Document(SRC)
doc=Document()

# A4 helpers.
def set_a4(sec, landscape=False):
    sec.top_margin=Cm(2); sec.bottom_margin=Cm(2); sec.left_margin=Cm(3); sec.right_margin=Cm(1.5)
    sec.header_distance=Cm(1); sec.footer_distance=Cm(1)
    if landscape:
        sec.orientation=1
        sec.page_width=Cm(29.7); sec.page_height=Cm(21)
    else:
        sec.orientation=0
        sec.page_width=Cm(21); sec.page_height=Cm(29.7)

def set_font(run,size=13,bold=False,italic=False):
    run.font.name="Times New Roman"; run.font.size=Pt(size); run.bold=bold; run.italic=italic

def format_body(p):
    p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
    pf=p.paragraph_format; pf.line_spacing=1.3; pf.space_before=Pt(6); pf.space_after=Pt(6); pf.first_line_indent=Cm(1)

def copy_paragraph(src_p, dst_doc, style=None):
    p=dst_doc.add_paragraph(style=style)
    for r in src_p.runs:
        nr=p.add_run(r.text)
        nr.bold=r.bold; nr.italic=r.italic; nr.underline=r.underline
        nr.font.name="Times New Roman"; nr.font.size=Pt(13); nr.bold=False; nr.italic=False; nr.font.color.rgb=None
    return p

def add_field(paragraph, code):
    run=paragraph.add_run()
    fldChar1=OxmlElement("w:fldChar"); fldChar1.set(qn("w:fldCharType"),"begin")
    instr=OxmlElement("w:instrText"); instr.set(qn("xml:space"),"preserve"); instr.text=code
    fldChar2=OxmlElement("w:fldChar"); fldChar2.set(qn("w:fldCharType"),"separate")
    text=OxmlElement("w:t"); text.text=" "
    fldChar3=OxmlElement("w:fldChar"); fldChar3.set(qn("w:fldCharType"),"end")
    run._r.extend([fldChar1,instr,fldChar2,text,fldChar3])
    return run

# SECTION 1 — COVER
sec=doc.sections[0]; set_a4(sec,False)
cover_texts=[
    ("BỘ GIÁO DỤC VÀ ĐÀO TẠO",13,False),
    ("TRƯỜNG ĐẠI HỌC THĂNG LONG",13,True),
]
for t,size,b in cover_texts:
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(4)
    r=p.add_run(t); set_font(r,size,b)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(8)
p.add_run().add_picture(str(LOGO),width=Cm(1.5))
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(20)
set_font(p.add_run("TIỂU LUẬN"),20,True)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(45)
set_font(p.add_run("CHIANG MAI"),17,True)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(75)
set_font(p.add_run("ĐÓA HỒNG PHƯƠNG BẮC XỨ CHÙA VÀNG"),17,True)
for label,value in [("SINH VIÊN THỰC HIỆN","NGUYỄN ĐẶNG PHƯƠNG NHI"),("MÃ SINH VIÊN","A57649"),("NGÀNH","KẾ TOÁN")]:
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.LEFT; p.paragraph_format.left_indent=Cm(6.8); p.paragraph_format.space_after=Pt(4)
    p.paragraph_format.tab_stops.add_tab_stop(Cm(10.2))
    set_font(p.add_run(label+":\t"+value),13,True)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before=Pt(150)
set_font(p.add_run("HÀ NỘI - 2026"),13,True)

# SECTION 2 — TOC
sec=doc.add_section(WD_SECTION.NEW_PAGE); set_a4(sec,False)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(12)
set_font(p.add_run("MỤC LỤC"),13,True)
p=doc.add_paragraph(); p.paragraph_format.left_indent=Cm(1)
add_field(p,'TOC \\o "1-3" \\h \\z \\u')

# SECTION 3 — illustration list
sec=doc.add_section(WD_SECTION.NEW_PAGE); set_a4(sec,False)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(12)
set_font(p.add_run("DANH MỤC MINH HỌA"),13,True)
p=doc.add_paragraph(); add_field(p,'TOC \\h \\z \\c "Ảnh"')
p=doc.add_paragraph(); add_field(p,'TOC \\h \\z \\c "Bảng"')

# SECTION 4 — portrait content
sec=doc.add_section(WD_SECTION.NEW_PAGE); set_a4(sec,False)
body_start=14
# first 23 paragraphs are the body before table; source has 1 table after para 37.
for idx in range(body_start, len(src.paragraphs)):
    sp=src.paragraphs[idx]
    p=copy_paragraph(sp,doc)
    t=p.text.strip()
    if t.startswith("CHƯƠNG 1.") or t.startswith("CHƯƠNG 2."):
        p.style="Heading 1"; p.alignment=WD_ALIGN_PARAGRAPH.LEFT
    elif t.startswith("2.1.") or t.startswith("2.2.") or t.startswith("2.3."):
        p.style="Heading 2"; p.alignment=WD_ALIGN_PARAGRAPH.LEFT
    elif t.startswith("2.2.1.") or t.startswith("2.2.2."):
        p.style="Heading 3"; p.alignment=WD_ALIGN_PARAGRAPH.LEFT
    elif t.startswith("- "):
        p.style="Normal"; p.paragraph_format.left_indent=Cm(1); p.paragraph_format.first_line_indent=Cm(-0.5)
        format_body(p)
    else:
        format_body(p)
        for rr in p.runs:
            rr.font.name="Times New Roman"; rr.font.size=Pt(13); rr.bold=False; rr.italic=False
        if t.startswith("Bạn có thể") or t.startswith("Để du lịch") or t.startswith("Giá vé"):
            pass

# Insert photo after the second paragraph of Chapter 1.
anchor=None
for p in doc.paragraphs:
    if p.text.startswith("Từng là thủ đô của một vương quốc hùng mạnh"):
        anchor=p; break
photo_p=doc.add_paragraph(); photo_p.alignment=WD_ALIGN_PARAGRAPH.CENTER
photo_p.paragraph_format.space_before=Pt(6); photo_p.paragraph_format.space_after=Pt(6)
photo=photo_p.add_run().add_picture(str(PHOTO),width=Cm(15))
# Move photo paragraph immediately after anchor.
anchor._p.addnext(photo_p._p)

# Caption placeholder under image.
cap=doc.add_paragraph("Ảnh 1.1. Chiang Mai mùa hoa nở")
cap.style="Caption"; cap.alignment=WD_ALIGN_PARAGRAPH.CENTER
cap.paragraph_format.space_before=Pt(6); cap.paragraph_format.space_after=Pt(6)
photo_p._p.addnext(cap._p)

# Add table section after current content, then table.
land=doc.add_section(WD_SECTION.NEW_PAGE); set_a4(land,True)
src_table=src.tables[0]
table=doc.add_table(rows=len(src_table.rows), cols=2)
table.alignment=WD_TABLE_ALIGNMENT.CENTER
table.autofit=False
# grid borders
tblPr=table._tbl.tblPr
borders=OxmlElement("w:tblBorders")
for edge in ("top","left","bottom","right","insideH","insideV"):
    e=OxmlElement("w:"+edge); e.set(qn("w:val"),"single"); e.set(qn("w:sz"),"6"); e.set(qn("w:color"),"000000"); borders.append(e)
tblPr.append(borders)
for i,row in enumerate(src_table.rows):
    for j,cell in enumerate(row.cells):
        table.cell(i,j).text=cell.text
        table.cell(i,j).vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
        table.cell(i,j).width=Cm(6 if j==0 else 20)
        for p in table.cell(i,j).paragraphs:
            p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY if i else WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before=Pt(0); p.paragraph_format.space_after=Pt(3); p.paragraph_format.line_spacing=1.3
            for r in p.runs: set_font(r,13,i==0)
# repeat header row
trPr=table.rows[0]._tr.get_or_add_trPr(); hdr=OxmlElement("w:tblHeader"); hdr.set(qn("w:val"),"true"); trPr.append(hdr)
# header shading
for c in table.rows[0].cells:
    tcPr=c._tc.get_or_add_tcPr(); shd=OxmlElement("w:shd"); shd.set(qn("w:fill"),"FCE4D6"); tcPr.append(shd)
cap=doc.add_paragraph("Bảng 2.1. Những điểm thăm quan nổi tiếng")
cap.style="Caption"; cap.alignment=WD_ALIGN_PARAGRAPH.CENTER
cap.paragraph_format.space_before=Pt(6); cap.paragraph_format.space_after=Pt(6)
# Move caption immediately before table.
table._tbl.addprevious(cap._p)

# Final paragraph after table.
p=doc.add_paragraph(src.paragraphs[-1].text)
format_body(p)

# Create/adjust styles.
styles=doc.styles
for name in ["Normal","Heading 1","Heading 2","Heading 3","Caption"]:
    s=styles[name]; s.font.name="Times New Roman"; s.font.size=Pt(13)
styles["Heading 1"].font.bold=True; styles["Heading 1"].paragraph_format.space_after=Pt(12)
styles["Heading 2"].font.bold=True
styles["Heading 3"].font.bold=True; styles["Heading 3"].font.italic=True
styles["Caption"].font.italic=True; styles["Caption"].paragraph_format.alignment=WD_ALIGN_PARAGRAPH.CENTER
styles["Caption"].paragraph_format.space_before=Pt(6); styles["Caption"].paragraph_format.space_after=Pt(6)

# Save.
doc.save(OUT)
print("BUILT",OUT)
print("sections",len(doc.sections),"paras",len(doc.paragraphs),"tables",len(doc.tables),"images",len(doc.inline_shapes))
