from pathlib import Path
p=Path(r"D:\LearningPesonal\Project\skiptlu\src\skiptlu\artifacts\word.py")
s=p.read_text(encoding="utf-8")
s=s.replace("doc = backend.open(spec.template_path)", "doc = backend.open(spec.template_path or spec.content_source_path)")
s=s.replace('''        metadata={"activity_id": spec.activity_id, "template": str(spec.template_path)},''',
            '''        metadata={
            "activity_id": spec.activity_id,
            "template": str(spec.template_path) if spec.template_path else None,
            "content_source": str(spec.content_source_path) if spec.content_source_path else None,
        },''')
p.write_text(s,encoding="utf-8")
print("patched")
