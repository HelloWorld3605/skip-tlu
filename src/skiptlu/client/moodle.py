from typing import Any

import httpx


class MoodleClient:
    """Thin HTTP client. Authentication/session details stay outside domain logic."""

    def __init__(self, base_url: str, cookies: dict[str, str] | None = None):
        self.base_url = base_url.rstrip("/")
        self.http = httpx.AsyncClient(
            base_url=self.base_url,
            cookies=cookies or {},
            follow_redirects=True,
            timeout=30,
        )

    async def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self.http.get(path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self.http.post(path, **kwargs)

    async def close(self) -> None:
        await self.http.aclose()
