import asyncio
from skiptlu.client.playwright import PlaywrightMoodleSession

async def main():
    s=PlaywrightMoodleSession(storage_state="storage_state.json")
    print("1")
    p=await s.open("https://elearning.thanglong.edu.vn/course/view.php?id=23946")
    print("2", p.title)
    h=await s.read_current_html()
    print("3", len(h), h.count("courseindex-link"), h.count("/mod/"))
    await s.close()
    print("4")

asyncio.run(main())
