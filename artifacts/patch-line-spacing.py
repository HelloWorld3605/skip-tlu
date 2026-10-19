from pathlib import Path
p=Path(r"D:\LearningPesonal\Project\skiptlu\artifacts\finalize-v5.py")
s=p.read_text(encoding="utf-8")
s=s.replace('p.Range.ParagraphFormat.SpaceBefore=0; p.Range.ParagraphFormat.SpaceAfter=3; p.Range.ParagraphFormat.LineSpacing=1.3',
            'p.Range.ParagraphFormat.SpaceBefore=0; p.Range.ParagraphFormat.SpaceAfter=3; p.Range.ParagraphFormat.LineSpacingRule=5; p.Range.ParagraphFormat.LineSpacing=16.9')
p.write_text(s,encoding="utf-8")
print("patched")
