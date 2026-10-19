from pathlib import Path
p=Path(r"D:\LearningPesonal\Project\skiptlu\artifacts\rebuild-week4-v4.py")
s=p.read_text(encoding="utf-8")
# Cover tab alignment: left-indent the whole student-info block so label/value stay on one line.
s=s.replace('p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(4)\n    p.paragraph_format.tab_stops.add_tab_stop(Cm(10))',
            'p.alignment=WD_ALIGN_PARAGRAPH.LEFT; p.paragraph_format.left_indent=Cm(6.8); p.paragraph_format.space_after=Pt(4)\n    p.paragraph_format.tab_stops.add_tab_stop(Cm(10.2))')
# Make every body run explicitly black, Times New Roman, 13, regular.
s=s.replace('nr.font.name="Times New Roman"; nr.font.size=Pt(13)',
            'nr.font.name="Times New Roman"; nr.font.size=Pt(13); nr.bold=False; nr.italic=False; nr.font.color.rgb=None')
# Force body paragraph run formatting after style assignment.
s=s.replace('else:\n        format_body(p)\n        if t.startswith("Bạn có thể")',
            'else:\n        format_body(p)\n        for rr in p.runs:\n            rr.font.name="Times New Roman"; rr.font.size=Pt(13); rr.bold=False; rr.italic=False\n        if t.startswith("Bạn có thể")')
# Force chapter 2 to start on a new page.
s=s.replace('elif t.startswith("2.1.") or t.startswith("2.2.") or t.startswith("2.3."):\n        p.style="Heading 2"',
            'elif t.startswith("2.1.") or t.startswith("2.2.") or t.startswith("2.3."):\n        p.style="Heading 2"')
# Add explicit page-break-before to chapter 2 after heading style loop.
needle='    # Insert photo after the second paragraph of Chapter 1.'
s=s.replace(needle, '    for p in doc.paragraphs:\n        if p.text.startswith("CHƯƠNG 2."):\n            p.paragraph_format.page_break_before=True\n            break\n\n'+needle)
# Table: increase spacing, add grid borders, repeat header.
s=s.replace('table.alignment=WD_TABLE_ALIGNMENT.CENTER\ntable.autofit=False',
            'table.alignment=WD_TABLE_ALIGNMENT.CENTER\ntable.autofit=False\n# grid borders\ntblPr=table._tbl.tblPr\nborders=OxmlElement("w:tblBorders")\nfor edge in ("top","left","bottom","right","insideH","insideV"):\n    e=OxmlElement("w:"+edge); e.set(qn("w:val"),"single"); e.set(qn("w:sz"),"6"); e.set(qn("w:color"),"000000"); borders.append(e)\ntblPr.append(borders)')
s=s.replace('p.paragraph_format.space_before=Pt(0); p.paragraph_format.space_after=Pt(0); p.paragraph_format.line_spacing=1.0',
            'p.paragraph_format.space_before=Pt(0); p.paragraph_format.space_after=Pt(3); p.paragraph_format.line_spacing=1.3')
# Header row repeat.
s=s.replace('# header shading\nfor c in table.rows[0].cells:',
            '# repeat header row\ntrPr=table.rows[0]._tr.get_or_add_trPr(); hdr=OxmlElement("w:tblHeader"); hdr.set(qn("w:val"),"true"); trPr.append(hdr)\n# header shading\nfor c in table.rows[0].cells:')
p.write_text(s,encoding="utf-8")
