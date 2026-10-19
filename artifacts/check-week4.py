import asyncio
from skiptlu.client.playwright import PlaywrightMoodleSession
from skiptlu.models.activity import Activity, ModuleType

async def main():
    s=PlaywrightMoodleSession(storage_state="storage_state.json")
    a=Activity(id=51068,module=ModuleType.ASSIGNMENT,name="Week 4 assignment",url="https://elearning.thanglong.edu.vn/mod/assign/view.php?id=51068")
    await s.open(a.url)
    r=await s.read_assignment_submission(a)
    print(r)
    await s.close()

asyncio.run(main())
