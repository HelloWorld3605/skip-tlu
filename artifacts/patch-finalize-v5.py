from pathlib import Path
p=Path(r"D:\LearningPesonal\Project\skiptlu\artifacts\finalize-v5.py")
s=p.read_text(encoding="utf-8")
old="""        for r in p.Range.Runs:
            r.Font.Name="Times New Roman"; r.Font.Size=13; r.Font.ColorIndex=0
            if not t.startswith("- "): r.Font.Bold=False; r.Font.Italic=False"""
new="""        p.Range.Font.Name="Times New Roman"; p.Range.Font.Size=13; p.Range.Font.ColorIndex=0
        if not t.startswith("- "): p.Range.Font.Bold=False; p.Range.Font.Italic=False"""
assert old in s
p.write_text(s.replace(old,new),encoding="utf-8")
print("patched")
