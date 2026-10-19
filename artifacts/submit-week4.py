import asyncio
from pathlib import Path
from skiptlu.client.playwright import PlaywrightMoodleSession
from skiptlu.models.activity import Activity, ModuleType

async def main():
    session = PlaywrightMoodleSession(storage_state="storage_state.json")
    activity = Activity(
        id=51068,
        module=ModuleType.ASSIGNMENT,
        name="[LUYỆN TẬP KIỂM TRA THỰC HÀNH] TÀI LIỆU CÓ NHIỀU CHƯƠNG, MỤC",
        url="https://elearning.thanglong.edu.vn/mod/assign/view.php?id=51068",
    )
    await session.open(activity.url)
    before = await session.read_assignment_submission(activity)
    print("BEFORE", before)
    artifact = list(Path("artifacts/week4/generated").glob("*.docx"))[0]
    print("FILE", artifact, artifact.stat().st_size)
    after = await session.submit_assignment(activity, artifact)
    print("AFTER", after)
    verified = await session.read_assignment_submission(activity)
    print("VERIFIED", verified)
    await session.close()

asyncio.run(main())
