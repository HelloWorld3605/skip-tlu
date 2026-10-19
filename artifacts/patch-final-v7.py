from pathlib import Path
p=Path(r"D:\LearningPesonal\Project\skiptlu\artifacts\finalize-v5.py")
s=p.read_text(encoding="utf-8")
s=s.replace('template.ListLevels(3).NumberFormat="%1.%2.%3."',
'''template.ListLevels(3).NumberFormat="%1.%2.%3."
    template.ListLevels(1).LinkedStyle="Heading 1"
    template.ListLevels(2).LinkedStyle="Heading 2"
    template.ListLevels(3).LinkedStyle="Heading 3"''')
s=s.replace('''    for i,row in enumerate(table.Rows, start=1):
        row.HeightRule=1
        row.Height=28 if i==1 else 68
        row.AllowBreakAcrossPages=True
    for row in table.Rows:''',
'''    table.AllowAutoFit=True
    table.AutoFitBehavior(2)
    table.Rows.HeightRule=0
    for row in table.Rows:
        row.AllowBreakAcrossPages=True
    for row in table.Rows:''')
p.write_text(s,encoding="utf-8")
print("patched")
