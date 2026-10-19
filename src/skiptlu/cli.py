import asyncio
from pathlib import Path

import typer
from rich import print

from skiptlu.artifacts.registry import ArtifactRegistry
from skiptlu.client.moodle import MoodleClient
from skiptlu.client.playwright import PlaywrightMoodleSession
from skiptlu.completion.engine import CompletionEngine
from skiptlu.handlers.router import HandlerRouter
from skiptlu.models.activity import Activity, ModuleType
from skiptlu.models.word_task import StudentInfo

app = typer.Typer(help="SkipTLU - Moodle/ELMS progress automation.")


@app.command()
def inspect(base_url: str = typer.Option(
    "https://elearning.thanglong.edu.vn",
    help="Moodle/ELMS base URL",
)):
    """Check that the ELMS endpoint is reachable."""
    async def run():
        client = MoodleClient(base_url)
        try:
            response = await client.get("/")
            print(f"[bold]HTTP:[/bold] {response.status_code}")
            print(f"[bold]URL:[/bold] {response.url}")
        finally:
            await client.close()

    asyncio.run(run())


@app.command()
def login(
    storage_state: Path = typer.Option(
        Path("storage_state.json"),
        "--storage-state",
        help="Where to save the authenticated Playwright state",
    ),
    base_url: str = typer.Option(
        "https://elearning.thanglong.edu.vn",
        "--base-url",
    ),
):
    """Open ELMS in a headed browser and save the authenticated session."""
    async def run():
        session = PlaywrightMoodleSession(headless=False, base_url=base_url)
        page = await session._ensure_page()
        await page.goto(base_url, wait_until="domcontentloaded")
        print("[bold]Browser opened.[/bold] Log in to ELMS, then return here.")
        input("Press Enter after login is complete... ")
        await session.save_storage_state(storage_state)
        print(f"[green]Saved storage state:[/green] {storage_state}")
        await session.close()

    asyncio.run(run())


@app.command("inspect-course")
def inspect_course(
    course_id: int = typer.Argument(..., help="Moodle course ID"),
    course_url: str = typer.Option(..., "--course-url", help="Full Moodle course URL"),
    storage_state: Path = typer.Option(
        Path("storage_state.json"),
        "--storage-state",
        help="Playwright authenticated storage-state JSON",
    ),
    base_url: str = typer.Option(
        "https://elearning.thanglong.edu.vn",
        "--base-url",
    ),
):
    """Discover a Moodle course and print a dependency/completion dry-run."""
    async def run():
        session = PlaywrightMoodleSession(
            headless=True,
            storage_state=storage_state,
            base_url=base_url,
        )
        try:
            await session.open(course_url)
            html = await session.read_current_html()
            from skiptlu.course.discovery import CourseDiscovery
            from skiptlu.completion.execution_planner import ExecutionPlanner
            from skiptlu.completion.planner import ProcessPlanner

            course = CourseDiscovery(None).parse_course_html(
                html,
                course_id=course_id,
                base_url=course_url,
            )
            planner = ProcessPlanner()
            execution = ExecutionPlanner().build(course.activities)
            snapshot = planner.snapshot(course.activities)

            print(f"[bold]Course:[/bold] {course.name}")
            print(f"[bold]Sections:[/bold] {len(course.sections)}")
            print(f"[bold]Activities:[/bold] {len(course.activities)}")
            print(f"[bold]Dependency cycles:[/bold] {len(execution.cycles)}")
            for section in course.sections:
                print(f"\n[bold]{section.name}[/bold] ({len(section.activities)})")
                for activity in section.activities:
                    state = snapshot.states[activity.id]
                    print(
                        f"  {activity.id} | {activity.module.value:10} | "
                        f"{activity.completion_status.value:10} | "
                        f"{state.availability.value:24} | {activity.name}"
                    )

            print("\n[bold]Execution order:[/bold]")
            print(" -> ".join(map(str, execution.ordered_activity_ids)))
            if execution.cycles:
                print(f"[red]Cycles:[/red] {execution.cycles}")
        finally:
            await session.close()

    asyncio.run(run())


@app.command("inspect-assignment")
def inspect_assignment(
    activity_id: int = typer.Argument(..., help="Moodle assignment activity ID"),
    storage_state: Path = typer.Option(
        Path("storage_state.json"),
        "--storage-state",
        help="Playwright authenticated storage-state JSON",
    ),
    base_url: str = typer.Option(
        "https://elearning.thanglong.edu.vn",
        "--base-url",
    ),
    download_dir: Path = typer.Option(
        Path("artifacts/references"),
        "--download-dir",
        help="Directory where Moodle reference files are downloaded",
    ),
):
    """Collect and print Moodle assignment context without submitting anything."""
    activity = Activity(
        id=activity_id,
        module=ModuleType.ASSIGNMENT,
        name=f"Moodle assignment {activity_id}",
        url=f"{base_url.rstrip('/')}/mod/assign/view.php?id={activity_id}",
    )

    async def run():
        session = PlaywrightMoodleSession(
            headless=True,
            storage_state=storage_state,
            base_url=base_url,
        )
        try:
            context = await session.collect_activity_context(activity)
            context = await session.download_references(context, download_dir / str(activity_id))
            print(f"[bold]Activity:[/bold] {context.activity.id}")
            print(f"[bold]Title:[/bold] {context.activity.name}")
            print(f"[bold]Instructions:[/bold] {len(context.instructions)}")
            for index, instruction in enumerate(context.instructions, 1):
                print(f"  {index}. {instruction}")
            print(f"[bold]Attachments:[/bold] {len(context.attachments)}")
            for attachment in context.attachments:
                print(f"  - {attachment.name}: {attachment.path or attachment.url}")
            print(f"[bold]Completion:[/bold] {context.metadata.get('completion', [])}")
        finally:
            await session.close()

    asyncio.run(run())


@app.command("run-assignment")
def run_assignment(
    activity_id: int = typer.Argument(..., help="Moodle activity ID"),
    student_name: str = typer.Option(..., "--student-name", prompt=True),
    student_id: str = typer.Option(..., "--student-id", prompt=True),
    major: str = typer.Option(..., "--major", prompt=True),
    storage_state: Path = typer.Option(
        Path("storage_state.json"),
        "--storage-state",
        help="Playwright authenticated storage-state JSON",
    ),
    headless: bool = typer.Option(False, "--headless/--headed"),
    base_url: str = typer.Option(
        "https://elearning.thanglong.edu.vn",
        "--base-url",
    ),
):
    """Generate the required artifact and submit a Moodle assignment."""
    activity = Activity(
        id=activity_id,
        module=ModuleType.ASSIGNMENT,
        name="[LUYỆN TẬP KIỂM TRA THỰC HÀNH] TÀI LIỆU CÓ NHIỀU CHƯƠNG, MỤC",
        url=f"{base_url.rstrip('/')}/mod/assign/view.php?id={activity_id}",
    )
    student = StudentInfo(
        name=student_name,
        student_id=student_id,
        major=major,
    )
    project_root = Path(__file__).resolve().parents[2]
    registry = ArtifactRegistry(project_root=project_root, student=student)

    async def run():
        session = PlaywrightMoodleSession(
            headless=headless,
            storage_state=storage_state,
            base_url=base_url,
        )
        router = HandlerRouter(session=session, artifact_registry=registry)
        engine = CompletionEngine(router)

        try:
            result = await engine.process(activity)
            print(f"[bold]Activity:[/bold] {result.activity_id}")
            print(f"[bold]Before:[/bold] {result.status_before.value}")
            print(f"[bold]After:[/bold] {result.status_after.value}")
            print(f"[bold]Changed:[/bold] {result.changed}")
            print(f"[bold]Message:[/bold] {result.message}")

            handler = router.for_activity(activity)
            execution = getattr(handler, "last_execution", None)
            if execution and execution.artifact_path:
                print(f"[bold]Artifact:[/bold] {execution.artifact_path}")
            if execution:
                print(f"[bold]Submission:[/bold] {execution.submission_submitted}")
                print(f"[bold]Verified:[/bold] {execution.completion_verified}")
        finally:
            await session.close()

    asyncio.run(run())


@app.command()
def architecture():
    """Print the current engine architecture."""
    print("""
[bold]SkipTLU[/bold]

Discovery
|
+-- Completion + Restriction Resolver
|
+-- Process Planner
|
+-- Handler Router
|   +-- lesson
|   +-- quiz
|   +-- assign
|   +-- feedback
|   +-- resource
|   +-- page
|   +-- h5pactivity
|
+-- Artifact Registry
|   +-- WordArtifactProvider (51068)
|   +-- future PPTX/XLSX providers
|
+-- Moodle Adapter
|   +-- Playwright
|
+-- Server Verification
""")


if __name__ == "__main__":
    app()
