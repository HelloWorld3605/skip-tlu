import asyncio
from pathlib import Path
from skiptlu.client.playwright import PlaywrightMoodleSession
from skiptlu.models.activity import Activity, ModuleType
from skiptlu.tasks.understanding import TaskUnderstandingEngine
from skiptlu.models.word_task import StudentInfo
from skiptlu.artifacts.registry import ArtifactRegistry

async def main():
    root=Path(".").resolve()
    activity=Activity(id=51068,module=ModuleType.ASSIGNMENT,name="[LUYỆN TẬP KIỂM TRA THỰC HÀNH] TÀI LIỆU CÓ NHIỀU CHƯƠNG, MỤC",url="https://elearning.thanglong.edu.vn/mod/assign/view.php?id=51068")
    session=PlaywrightMoodleSession(storage_state="storage_state.json")
    await session.open(activity.url)
    context=await session.collect_activity_context(activity)
    context=await session.download_references(context,root/"artifacts"/"week4")
    context=await session.parse_references(context)
    spec=TaskUnderstandingEngine().understand(context)

    # Week 4 has stable local fixtures downloaded under artifacts/week4.
    # Bind the known template/content roles explicitly so the document test
    # does not depend on the Moodle attachment/session state.
    week4_dir = root / "artifacts" / "week4"
    template_pdf = week4_dir / "File mẫu THAM KHẢO_ThamKhao_LuyenTap_BaiSo1.pdf"
    content_docx = week4_dir / "File BÀI LÀM_BaiLam_LuyenTap_BaiSo1.docx"
    image_file = week4_dir / "Ảnh chèn vào bài làm_Picture_De1.jpg"
    if template_pdf.is_file() and content_docx.is_file():
        spec.metadata["artifact_strategy"] = "use_template"
        # The supplied Word file is the editable master; the PDF is kept
        # as a formatting/reference source and is never modified.
        spec.metadata["template_files"] = [str(content_docx)]
        spec.metadata["content_files"] = [str(content_docx)]
        spec.source_files = list(dict.fromkeys([*spec.source_files, template_pdf, content_docx, image_file]))

    student=StudentInfo(name="Nguyễn Đặng Phương Nhi",student_id="A57649",major="Kế toán")
    registry=ArtifactRegistry(project_root=root,student=student,output_dir=root/"artifacts"/"week4"/"generated")
    provider=registry.for_task(spec,activity)
    if provider is None: raise RuntimeError("No artifact provider")
    artifact=await provider.prepare(activity,spec)
    print("ARTIFACT",artifact.path)
    print("KIND",artifact.kind)
    print("METADATA_KEYS", sorted(artifact.metadata))
    await session.close()

asyncio.run(main())
