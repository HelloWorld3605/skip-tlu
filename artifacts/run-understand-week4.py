import asyncio, json
from pathlib import Path
from skiptlu.client.playwright import PlaywrightMoodleSession
from skiptlu.models.activity import Activity, ModuleType
from skiptlu.tasks.understanding import TaskUnderstandingEngine

async def main():
    a=Activity(id=51068,module=ModuleType.ASSIGNMENT,name="[LUYỆN TẬP KIỂM TRA THỰC HÀNH] TÀI LIỆU CÓ NHIỀU CHƯƠNG, MỤC",url="https://elearning.thanglong.edu.vn/mod/assign/view.php?id=51068")
    s=PlaywrightMoodleSession(storage_state="storage_state.json")
    await s.open(a.url)
    c=await s.collect_activity_context(a)
    c=await s.download_references(c,Path("artifacts/week4"))
    c=await s.parse_references(c)
    print("instructions",len(c.instructions))
    print("attachments",[(x.name,str(x.path)) for x in c.attachments])
    print("parsed",[(str(x.path),x.file_type,len(x.paragraphs),len(x.tables),len(x.images),x.hints.headings,x.hints.captions) for x in c.parsed_references])
    spec=TaskUnderstandingEngine().understand(c)
    Path("artifacts/week4/spec.json").write_text(spec.model_dump_json(indent=2),encoding="utf-8")
    print("spec",spec.model_dump_json(indent=2)[:5000])
    await s.close()

asyncio.run(main())
