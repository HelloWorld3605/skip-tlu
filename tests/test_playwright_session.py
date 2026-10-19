import asyncio

from skiptlu.client.playwright import PlaywrightMoodleSession


def test_playwright_session_can_launch_and_close():
    async def run():
        session = PlaywrightMoodleSession(headless=True)
        page = await session._ensure_page()
        assert page is not None
        await session.close()

    asyncio.run(run())
