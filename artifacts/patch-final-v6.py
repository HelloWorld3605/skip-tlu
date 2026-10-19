from pathlib import Path
p=Path(r"D:\LearningPesonal\Project\skiptlu\artifacts\finalize-v5.py")
s=p.read_text(encoding="utf-8")
s=s.replace('template=word.ListGalleries(3).ListTemplates(2)',
'''template=word.ListGalleries(3).ListTemplates(2)
    template.ListLevels(1).NumberFormat="CHƯƠNG %1."
    template.ListLevels(2).NumberFormat="%1.%2."
    template.ListLevels(3).NumberFormat="%1.%2.%3."''')
s=s.replace('table=doc.Tables(1)\n    for row in table.Rows:',
'''table=doc.Tables(1)
    # Make the landscape table readable and force it to flow across two pages like the sample.
    for i,row in enumerate(table.Rows, start=1):
        row.HeightRule=1
        row.Height=28 if i==1 else 68
        row.AllowBreakAcrossPages=True
    for row in table.Rows:''')
p.write_text(s,encoding="utf-8")
print("patched")
