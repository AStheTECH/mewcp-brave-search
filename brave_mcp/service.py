"""Brave Search API client layer — the only module that touches credentials.

get_credentials() is called per request, inside this module, never cached
in a global and never passed up to tools.py.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from fastmcp_credentials import get_credentials

from .config import BRAVE_API_BASE, CONNECT_TIMEOUT, ENDPOINT_MAP, READ_TIMEOUT
from .utils import check_rate_limit

_client = httpx.AsyncClient(
    base_url=BRAVE_API_BASE,
    timeout=httpx.Timeout(connect=CONNECT_TIMEOUT, read=READ_TIMEOUT),
)

_MAX_POLLS = 20
_POLL_INTERVAL = 0.05  # 50 ms — matches summarizer/index.ts


def _get_headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    cred = get_credentials()
    api_key = cred.fields.get("api_key")
    if not api_key:
        raise ValueError("Missing 'api_key' credential field")
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key,
    }
    if extra:
        headers.update(extra)
    return headers


def _build_query(params: dict[str, Any]) -> list[tuple[str, Any]]:
    skip_result_filter = bool(params.get("summary"))
    query: list[tuple[str, Any]] = []
    for key, value in params.items():
        if value is None:
            continue
        if key == "result_filter" and skip_result_filter:
            continue
        if key in ("ids", "result_filter") and isinstance(value, (list, tuple)):
            query.extend((key, item) for item in value)
            continue
        if key == "goggles":
            goggles = [value] if isinstance(value, str) else list(value)
            query.extend(("goggles", g) for g in goggles if g.startswith("https://"))
            continue
        query.append((key, value))
    return query


async def make_brave_request(
    endpoint_type: str,
    params: dict[str, Any],
    extra_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Issue one Brave API request. Returns {"ok": True, "data": ...} or {"ok": False, "error": ...}."""
    try:
        check_rate_limit()
        headers = _get_headers(extra_headers)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

    path = ENDPOINT_MAP[endpoint_type]
    query = _build_query(params)

    try:
        r = await _client.get(path, params=query, headers=headers)
    except httpx.HTTPError as exc:
        return {"ok": False, "error": f"Request to Brave API failed: {exc}"}

    if not r.is_success:
        try:
            body: Any = r.json()
        except Exception:
            body = r.text
        return {"ok": False, "error": f"Brave API {r.status_code}: {body}"}

    return {"ok": True, "data": r.json()}


# ── result formatters ────────────────────────────────────────────────────────

def _fmt_web_results(web: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "url": r.get("url"),
            "title": r.get("title"),
            "description": r.get("description"),
            "extra_snippets": r.get("extra_snippets"),
        }
        for r in web.get("results", [])
    ]


def _fmt_faq_results(faq: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "question": r.get("question"),
            "answer": r.get("answer"),
            "title": r.get("title"),
            "url": r.get("url"),
        }
        for r in faq.get("results", [])
    ]


def _fmt_discussion_results(discussions: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "mutated_by_goggles": discussions.get("mutated_by_goggles"),
            "url": r.get("url"),
            "data": r.get("data"),
        }
        for r in discussions.get("results", [])
    ]


def _fmt_news_results(news: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "mutated_by_goggles": news.get("mutated_by_goggles"),
            "source": r.get("source"),
            "breaking": r.get("breaking"),
            "is_live": r.get("is_live"),
            "age": r.get("age"),
            "url": r.get("url"),
            "title": r.get("title"),
            "description": r.get("description"),
            "extra_snippets": r.get("extra_snippets"),
        }
        for r in news.get("results", [])
    ]


def _fmt_video_results(videos: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "mutated_by_goggles": videos.get("mutated_by_goggles"),
            "url": r.get("url"),
            "title": r.get("title"),
            "description": r.get("description"),
            "age": r.get("age"),
            "thumbnail_url": (r.get("thumbnail") or {}).get("src"),
            "duration": (r.get("video") or {}).get("duration"),
            "view_count": (r.get("video") or {}).get("views"),
            "creator": (r.get("video") or {}).get("creator"),
            "publisher": (r.get("video") or {}).get("publisher"),
            "tags": (r.get("video") or {}).get("tags"),
        }
        for r in videos.get("results", [])
    ]


def _fmt_image_results(images: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "url": (r.get("properties") or {}).get("url") or r.get("url"),
            "source": r.get("source"),
            "title": r.get("title"),
            "width": (r.get("properties") or {}).get("width"),
            "height": (r.get("properties") or {}).get("height"),
            "format": (r.get("properties") or {}).get("format"),
        }
        for r in images.get("results", [])
    ]


def _fmt_poi(poi: dict[str, Any], desc_map: dict[str, list[str]]) -> dict[str, Any]:
    addr = poi.get("address", {})
    rating = poi.get("rating", {})
    hours_raw = poi.get("openingHours", [])

    return {
        "name": poi.get("name"),
        "address": ", ".join(
            filter(None, [
                addr.get("streetAddress"),
                addr.get("addressLocality"),
                addr.get("addressRegion"),
                addr.get("postalCode"),
            ])
        ),
        "phone": poi.get("phone") or (poi.get("contact") or {}).get("phone"),
        "rating": rating.get("ratingValue"),
        "review_count": rating.get("reviewCount"),
        "hours": hours_raw,
        "price_range": poi.get("priceRange"),
        "categories": poi.get("categories", []),
        "url": poi.get("url"),
        "description": (desc_map.get(poi.get("id", ""), []) or [None])[0],
    }


def _fmt_summary_text(summary_items: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for item in summary_items:
        t = item.get("type")
        if t == "token":
            parts.append(item.get("data", ""))
        elif t == "inlineLocation":
            parts.append(f"[{item.get('title', '')}]({item.get('url', '')})")
    return "".join(parts)


# ── domain operations (called by tools.py; return {"error": ...} on failure) ──

async def web_search(params: dict[str, Any]) -> dict[str, Any]:
    res = await make_brave_request("web", params)
    if not res["ok"]:
        return {"error": res["error"]}
    data = res["data"]

    entries: list[Any] = []
    summarizer = data.get("summarizer")
    if summarizer and summarizer.get("key"):
        entries.append({"summarizer_key": summarizer["key"]})

    web = data.get("web")
    if not web or not web.get("results"):
        return {"error": "No web results found"}
    entries.extend(_fmt_web_results(web))

    faq = data.get("faq")
    if faq and faq.get("results"):
        entries.extend(_fmt_faq_results(faq))

    discussions = data.get("discussions")
    if discussions and discussions.get("results"):
        entries.extend(_fmt_discussion_results(discussions))

    news = data.get("news")
    if news and news.get("results"):
        entries.extend(_fmt_news_results(news))

    videos = data.get("videos")
    if videos and videos.get("results"):
        entries.extend(_fmt_video_results(videos))

    return {"results": entries}


async def local_search(query: str, count: int, country: str) -> dict[str, Any]:
    res = await make_brave_request(
        "web",
        {"q": query, "count": count, "country": country, "result_filter": ["locations", "web"]},
    )
    if not res["ok"]:
        return {"error": res["error"]}
    data = res["data"]

    locations = data.get("locations", {})
    location_results: list[dict] = locations.get("results", [])
    ids = [r["id"] for r in location_results[:20] if r.get("id")]

    if not ids:
        web = data.get("web", {})
        web_results = web.get("results", [])
        if not web_results:
            return {"error": "No local or web results found"}
        return {"results": _fmt_web_results(web)}

    pois_res, desc_res = await asyncio.gather(
        make_brave_request("localPois", {"ids": ids}),
        make_brave_request("localDescriptions", {"ids": ids}),
    )
    if not pois_res["ok"]:
        return {"error": pois_res["error"]}
    if not desc_res["ok"]:
        return {"error": desc_res["error"]}

    pois: list[dict] = pois_res["data"].get("results", [])
    desc_map: dict[str, list[str]] = {
        d.get("id", ""): d.get("descriptions", [])
        for d in desc_res["data"].get("results", [])
    }
    return {"results": [_fmt_poi(p, desc_map) for p in pois]}


async def video_search(params: dict[str, Any]) -> dict[str, Any]:
    res = await make_brave_request("videos", params)
    if not res["ok"]:
        return {"error": res["error"]}
    if not res["data"].get("results"):
        return {"error": "No video results found"}
    return {"results": _fmt_video_results(res["data"])}


async def image_search(params: dict[str, Any]) -> dict[str, Any]:
    res = await make_brave_request("images", params)
    if not res["ok"]:
        return {"error": res["error"]}
    if not res["data"].get("results"):
        return {"error": "No image results found"}
    return {"results": _fmt_image_results(res["data"])}


async def news_search(params: dict[str, Any]) -> dict[str, Any]:
    res = await make_brave_request("news", params)
    if not res["ok"]:
        return {"error": res["error"]}
    if not res["data"].get("results"):
        return {"error": "No news results found"}
    return {"results": _fmt_news_results(res["data"])}


async def place_search(params: dict[str, Any]) -> dict[str, Any]:
    res = await make_brave_request("placeSearch", params)
    if not res["ok"]:
        return {"error": res["error"]}
    results = res["data"].get("results", [])
    if not results:
        return {"error": "No place results found"}
    return {"results": [_fmt_poi(p, {}) for p in results]}


async def summarize(key: str, entity_info: bool) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for _ in range(_MAX_POLLS):
        res = await make_brave_request(
            "summarizer", {"key": key, "entity_info": str(entity_info).lower()}
        )
        if not res["ok"]:
            return {"error": res["error"]}
        data = res["data"]
        if data.get("status") != "incomplete" and data.get("summary"):
            break
        await asyncio.sleep(_POLL_INTERVAL)
    else:
        return {"error": "Summary generation timed out"}

    summary_items = data.get("summary", [])
    text = _fmt_summary_text(summary_items) if isinstance(summary_items, list) else str(summary_items)
    if not text:
        return {"error": "No summary content returned"}
    return {"text": text}


async def llm_context(params: dict[str, Any], extra_headers: dict[str, str] | None) -> dict[str, Any]:
    res = await make_brave_request("llmContext", params, extra_headers=extra_headers)
    if not res["ok"]:
        return {"error": res["error"]}
    return {"data": res["data"]}


async def aclose() -> None:
    await _client.aclose()
