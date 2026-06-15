"""BraveSearchService — mirrors BraveAPI/index.ts issueRequest pattern."""

from __future__ import annotations

from typing import Any

import httpx

from .config import Settings
from .utils import check_rate_limit

_API_BASE = "https://api.search.brave.com"

# Matches typeToPathMap in BraveAPI/index.ts
_ENDPOINT_MAP: dict[str, str] = {
    "web": "/res/v1/web/search",
    "videos": "/res/v1/videos/search",
    "images": "/res/v1/images/search",
    "news": "/res/v1/news/search",
    "local": "/res/v1/local/search",
    "localPois": "/res/v1/local/pois",
    "localDescriptions": "/res/v1/local/descriptions",
    "summarizer": "/res/v1/summarizer/search",
    "llmContext": "/res/v1/llm/context",
    "placeSearch": "/res/v1/local/place_search",
}


class BraveSearchService:
    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.api_key
        self._client = httpx.AsyncClient(
            base_url=_API_BASE,
            timeout=httpx.Timeout(30.0),
        )

    async def issue_request(
        self,
        endpoint_type: str,
        params: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Mirror of issueRequest() in BraveAPI/index.ts."""
        check_rate_limit()
        path = _ENDPOINT_MAP[endpoint_type]

        req_headers: dict[str, str] = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self._api_key,
        }
        if headers:
            req_headers.update(headers)

        # Build query params — some require repeated keys (arrays)
        skip_result_filter = bool(params.get("summary"))
        query: list[tuple[str, Any]] = []

        for key, value in params.items():
            if value is None:
                continue

            # Skip result_filter when summary is enabled (deprecated endpoint)
            if key == "result_filter" and skip_result_filter:
                continue

            # Array params: repeat the key per value
            if key in ("ids", "result_filter") and isinstance(value, (list, tuple)):
                for item in value:
                    query.append((key, item))
                continue

            # Goggles: only allow HTTPS URLs, support multiple
            if key == "goggles":
                goggles = [value] if isinstance(value, str) else list(value)
                for g in goggles:
                    if g.startswith("https://"):
                        query.append(("goggles", g))
                continue

            query.append((key, value))

        r = await self._client.get(path, params=query, headers=req_headers)

        if not r.is_success:
            try:
                body: Any = r.json()
            except Exception:
                body = r.text
            raise httpx.HTTPStatusError(
                f"Brave API {r.status_code}: {body}",
                request=r.request,
                response=r,
            )

        return r.json()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> BraveSearchService:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.aclose()
