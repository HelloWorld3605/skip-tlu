from pathlib import Path
p=Path(r"D:\LearningPesonal\Project\skiptlu\artifacts\finalize-v9.py")
s=p.read_text(encoding="utf-8")
old='''if new.startswith("CHƯƠNG 2."):
            try:
                prev=p.Previous()
                rr=prev.Range.Duplicate
                rr.Collapse(0)
                rr.InsertBreak(7)
            except:
                pass'''
new='''if new.startswith("CHƯƠNG 2."):
            try:
                p.Range.InsertParagraphBefore()
                prev=p.Previous()
                prev.Range.InsertBreak(7)
            except:
                pass'''
assert old in s
p.write_text(s.replace(old,new),encoding="utf-8")
print("patched")
