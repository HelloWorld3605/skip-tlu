from pathlib import Path
p=Path(r"D:\LearningPesonal\Project\skiptlu\src\skiptlu\tasks\understanding.py")
s=p.read_text(encoding="utf-8")
s=s.replace(
'from skiptlu.tasks.reference_roles import classify_reference_roles',
'from skiptlu.tasks.reference_roles import classify_reference_roles\nfrom skiptlu.tasks.content_operations import ContentOperation'
)
old='''        metadata = {
            "description": context.description,
'''
new='''        raw_operations = context.metadata.get("content_operations", [])
        content_operations = [
            ContentOperation.model_validate(item)
            for item in raw_operations
            if isinstance(item, dict)
        ]
        metadata = {
            "description": context.description,
'''
s=s.replace(old,new)
s=s.replace(
'            "content_operations": context.metadata.get("content_operations", []),',
'            "content_operations": [item.model_dump() for item in content_operations],'
)
s=s.replace(
'            content=content,
            layout=default_word_layout(',
'            content=content,
            layout=default_word_layout('
)
# Insert field before metadata in returned model.
s=s.replace(
'            layout=default_word_layout(
                include_toc=content.include_toc,
                include_landscape=content.include_landscape_section,
            ),
            metadata=metadata,',
'            layout=default_word_layout(
                include_toc=content.include_toc,
                include_landscape=content.include_landscape_section,
            ),
            content_operations=content_operations,
            metadata=metadata,'
)
p.write_text(s,encoding="utf-8")
print("patched")
