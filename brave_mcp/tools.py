"""
Register all 8 Brave Search tools — mirrors tools/index.ts structure.

Each tool:
  - Uses Brave's exact param enums (country, search_lang, ui_lang)
  - Returns one TextContent(type='text', text=stringify(entry)) per result item
  - Carries ToolAnnotations(title=..., openWorldHint=True)
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Annotated, Optional

from mcp.types import TextContent, ToolAnnotations
from pydantic import Field

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from .config import Settings
    from .service import BraveSearchService

from . import schemas as S
from .utils import stringify

_MAX_POLLS = 20
_POLL_INTERVAL = 0.05  # 50 ms — matches summarizer/index.ts


def register(server: FastMCP, svc: BraveSearchService, settings: Settings) -> None:

    # ── brave_web_search ──────────────────────────────────────────────────────
    if settings.is_tool_permitted("brave_web_search"):

        @server.tool(
            description=(
                "Performs web searches using the Brave Search API and returns comprehensive "
                "search results with rich metadata.\n\n"
                "When to use:\n"
                "  - General web searches for information, facts, or current topics\n"
                "  - Location-based queries (restaurants, businesses, points of interest)\n"
                "  - News searches for recent events or breaking stories\n"
                "  - Finding videos, discussions, or FAQ content\n\n"
                "Returns a JSON list of web results with title, description, and URL. "
                "When result_filter is empty, results may also contain FAQ, Discussions, "
                "News, and Video items."
            ),
            annotations=ToolAnnotations(title="Brave Web Search", openWorldHint=True),
        )
        async def brave_web_search(
            query: Annotated[str, Field(description="Search query (max 400 chars, 50 words)")],
            country: Annotated[S.CountryCode, Field(description="Country for results")] = "US",
            search_lang: Annotated[S.SearchLang, Field(description="Search language")] = "en",
            ui_lang: Annotated[S.UiLang, Field(description="UI language")] = "en-US",
            count: Annotated[int, Field(description="Number of web results (1–20)", ge=1, le=20)] = 10,
            offset: Annotated[int, Field(description="Pagination offset (0–9)", ge=0, le=9)] = 0,
            safesearch: Annotated[S.SafeSearch, Field(description="Safe-search level")] = "moderate",
            freshness: Annotated[
                Optional[str],
                Field(description="Time filter: pd (day) pw (week) pm (month) py (year) or YYYY-MM-DDtoYYYY-MM-DD"),
            ] = None,
            text_decorations: Annotated[bool, Field(description="Include decoration markers in snippets")] = True,
            spellcheck: Annotated[bool, Field(description="Spellcheck the query")] = True,
            result_filter: Annotated[
                Optional[list[S.ResultFilter]],
                Field(description="Subset of result types to return (default ['web','query'])"),
            ] = None,
            goggles: Annotated[
                Optional[list[str]],
                Field(description="Goggle HTTPS URLs for custom re-ranking"),
            ] = None,
            units: Annotated[Optional[S.Units], Field(description="Measurement units")] = None,
            extra_snippets: Annotated[
                Optional[bool],
                Field(description="Up to 5 extra excerpts per result (Pro plan)"),
            ] = None,
            summary: Annotated[
                Optional[bool],
                Field(description="Return a summarizer_key to pass to brave_summarizer"),
            ] = None,
        ) -> list[TextContent]:
            response = await svc.issue_request(
                "web",
                {
                    "q": query,
                    "country": country,
                    "search_lang": search_lang,
                    "ui_lang": ui_lang,
                    "count": count,
                    "offset": offset,
                    "safesearch": safesearch,
                    "freshness": freshness,
                    "text_decorations": text_decorations,
                    "spellcheck": spellcheck,
                    "result_filter": result_filter,
                    "goggles": goggles,
                    "units": units,
                    "extra_snippets": extra_snippets,
                    "summary": summary,
                },
            )

            content: list[TextContent] = []

            summarizer = response.get("summarizer")
            if summarizer and summarizer.get("key"):
                content.append(TextContent(type="text", text=f"Summarizer key: {summarizer['key']}"))

            web = response.get("web")
            if not web or not web.get("results"):
                raise ValueError("No web results found")

            for entry in S.fmt_web_results(web):
                content.append(TextContent(type="text", text=stringify(entry)))

            faq = response.get("faq")
            if faq and faq.get("results"):
                for entry in S.fmt_faq_results(faq):
                    content.append(TextContent(type="text", text=stringify(entry)))

            discussions = response.get("discussions")
            if discussions and discussions.get("results"):
                for entry in S.fmt_discussion_results(discussions):
                    content.append(TextContent(type="text", text=stringify(entry)))

            news = response.get("news")
            if news and news.get("results"):
                for entry in S.fmt_news_results(news):
                    content.append(TextContent(type="text", text=stringify(entry)))

            videos = response.get("videos")
            if videos and videos.get("results"):
                for entry in S.fmt_video_results(videos):
                    content.append(TextContent(type="text", text=stringify(entry)))

            return content

    # ── brave_local_search ────────────────────────────────────────────────────
    if settings.is_tool_permitted("brave_local_search"):

        @server.tool(
            description=(
                "Searches for local businesses and places via the Brave Search API. "
                "Returns ratings, addresses, phone numbers, hours, and AI descriptions.\n\n"
                "Access to enriched POI data requires a Brave Search API Pro plan; "
                "the tool gracefully falls back to web results if local data is unavailable."
            ),
            annotations=ToolAnnotations(title="Brave Local Search", openWorldHint=True),
        )
        async def brave_local_search(
            query: Annotated[str, Field(description="Local search query, e.g. 'pizza near downtown Chicago'")],
            count: Annotated[int, Field(description="Results to return (1–20)", ge=1, le=20)] = 5,
            country: Annotated[S.CountryCode, Field(description="Country code")] = "US",
        ) -> list[TextContent]:
            # Step 1: web search to get location IDs
            response = await svc.issue_request(
                "web",
                {
                    "q": query,
                    "count": count,
                    "country": country,
                    "result_filter": ["locations", "web"],
                },
            )

            locations = response.get("locations", {})
            location_results: list[dict] = locations.get("results", [])
            ids = [r["id"] for r in location_results[:20] if r.get("id")]

            # Fallback: return web results when no local data
            if not ids:
                web = response.get("web", {})
                web_results = web.get("results", [])
                if not web_results:
                    raise ValueError("No local or web results found")
                return [
                    TextContent(type="text", text=stringify(e))
                    for e in S.fmt_web_results(web)
                ]

            # Step 2: fetch POI details and AI descriptions
            pois_resp, desc_resp = await asyncio.gather(
                svc.issue_request("localPois", {"ids": ids}),
                svc.issue_request("localDescriptions", {"ids": ids}),
            )

            pois: list[dict] = pois_resp.get("results", [])
            desc_map: dict[str, list[str]] = {
                d.get("id", ""): d.get("descriptions", [])
                for d in desc_resp.get("results", [])
            }

            return [
                TextContent(type="text", text=stringify(S.fmt_poi(p, desc_map)))
                for p in pois
            ]

    # ── brave_video_search ────────────────────────────────────────────────────
    if settings.is_tool_permitted("brave_video_search"):

        @server.tool(
            description="Searches for videos via the Brave Search API. Returns titles, URLs, durations, view counts, creators, and thumbnails.",
            annotations=ToolAnnotations(title="Brave Video Search", openWorldHint=True),
        )
        async def brave_video_search(
            query: Annotated[str, Field(description="Video search query (max 400 chars, 50 words)")],
            country: Annotated[S.CountryCode, Field(description="Country for results")] = "US",
            search_lang: Annotated[S.SearchLang, Field(description="Search language")] = "en",
            ui_lang: Annotated[S.UiLang, Field(description="UI language")] = "en-US",
            count: Annotated[int, Field(description="Results to return (1–20)", ge=1, le=20)] = 10,
            offset: Annotated[int, Field(description="Pagination offset (0–9)", ge=0, le=9)] = 0,
            safesearch: Annotated[S.SafeSearch, Field(description="Safe-search level")] = "moderate",
            freshness: Annotated[
                Optional[str],
                Field(description="Time filter: pd pw pm py or YYYY-MM-DDtoYYYY-MM-DD"),
            ] = None,
            spellcheck: Annotated[bool, Field(description="Spellcheck the query")] = True,
        ) -> list[TextContent]:
            response = await svc.issue_request(
                "videos",
                {
                    "q": query,
                    "country": country,
                    "search_lang": search_lang,
                    "ui_lang": ui_lang,
                    "count": count,
                    "offset": offset,
                    "safesearch": safesearch,
                    "freshness": freshness,
                    "spellcheck": spellcheck,
                },
            )
            results = response.get("results", [])
            if not results:
                raise ValueError("No video results found")
            return [
                TextContent(type="text", text=stringify(e))
                for e in S.fmt_video_results(response)
            ]

    # ── brave_image_search ────────────────────────────────────────────────────
    if settings.is_tool_permitted("brave_image_search"):

        @server.tool(
            description=(
                "Searches for images via the Brave Search API. "
                "Returns direct image URLs, source pages, and dimensions. "
                "Images are returned as URLs — no base64 encoding."
            ),
            annotations=ToolAnnotations(title="Brave Image Search", openWorldHint=True),
        )
        async def brave_image_search(
            query: Annotated[str, Field(description="Image search query (max 400 chars, 50 words)")],
            country: Annotated[S.CountryCode, Field(description="Country for results")] = "US",
            search_lang: Annotated[S.SearchLang, Field(description="Search language")] = "en",
            count: Annotated[int, Field(description="Results to return (1–20)", ge=1, le=20)] = 10,
            safesearch: Annotated[S.SafeSearch, Field(description="Safe-search level")] = "moderate",
            spellcheck: Annotated[bool, Field(description="Spellcheck the query")] = True,
        ) -> list[TextContent]:
            response = await svc.issue_request(
                "images",
                {
                    "q": query,
                    "country": country,
                    "search_lang": search_lang,
                    "count": count,
                    "safesearch": safesearch,
                    "spellcheck": spellcheck,
                },
            )
            results = response.get("results", [])
            if not results:
                raise ValueError("No image results found")
            return [
                TextContent(type="text", text=stringify(e))
                for e in S.fmt_image_results(response)
            ]

    # ── brave_news_search ─────────────────────────────────────────────────────
    if settings.is_tool_permitted("brave_news_search"):

        @server.tool(
            description="Searches for current news articles via the Brave Search API. Returns headlines, sources, publication age, and descriptions.",
            annotations=ToolAnnotations(title="Brave News Search", openWorldHint=True),
        )
        async def brave_news_search(
            query: Annotated[str, Field(description="News search query (max 400 chars, 50 words)")],
            country: Annotated[S.CountryCode, Field(description="Country for results")] = "US",
            search_lang: Annotated[S.SearchLang, Field(description="Search language")] = "en",
            ui_lang: Annotated[S.UiLang, Field(description="UI language")] = "en-US",
            count: Annotated[int, Field(description="Results to return (1–20)", ge=1, le=20)] = 10,
            offset: Annotated[int, Field(description="Pagination offset (0–9)", ge=0, le=9)] = 0,
            safesearch: Annotated[S.SafeSearch, Field(description="Safe-search level")] = "moderate",
            freshness: Annotated[
                Optional[str],
                Field(description="Time filter: pd pw pm py or YYYY-MM-DDtoYYYY-MM-DD"),
            ] = None,
            extra_snippets: Annotated[
                Optional[bool],
                Field(description="Up to 5 extra excerpts per result (Pro plan)"),
            ] = None,
            spellcheck: Annotated[bool, Field(description="Spellcheck the query")] = True,
        ) -> list[TextContent]:
            response = await svc.issue_request(
                "news",
                {
                    "q": query,
                    "country": country,
                    "search_lang": search_lang,
                    "ui_lang": ui_lang,
                    "count": count,
                    "offset": offset,
                    "safesearch": safesearch,
                    "freshness": freshness,
                    "extra_snippets": extra_snippets,
                    "spellcheck": spellcheck,
                },
            )
            results = response.get("results", [])
            if not results:
                raise ValueError("No news results found")
            return [
                TextContent(type="text", text=stringify(e))
                for e in S.fmt_news_results(response)
            ]

    # ── brave_place_search ────────────────────────────────────────────────────
    if settings.is_tool_permitted("brave_place_search"):

        @server.tool(
            description=(
                "Retrieves points of interest (POIs) with structured business data via "
                "Brave's dedicated place-search endpoint. Returns addresses, hours, "
                "ratings, categories, and contact info.\n\n"
                "Geographic context is required — provide latitude/longitude or a "
                "location string (e.g. 'san francisco ca united states').\n\n"
                "Access requires a Brave Search API Pro plan."
            ),
            annotations=ToolAnnotations(title="Brave Place Search", openWorldHint=True),
        )
        async def brave_place_search(
            query: Annotated[str, Field(description="Search query — shapes result type, e.g. 'coffee shops' or 'Eiffel Tower'")],
            location: Annotated[
                Optional[str],
                Field(description="Location context, e.g. 'san francisco ca united states' or 'tokyo japan'"),
            ] = None,
            latitude: Annotated[
                Optional[float],
                Field(description="Latitude (-90 to 90)", ge=-90, le=90),
            ] = None,
            longitude: Annotated[
                Optional[float],
                Field(description="Longitude (-180 to 180)", ge=-180, le=180),
            ] = None,
            radius: Annotated[
                Optional[int],
                Field(description="Proximity bias in metres (not a hard cutoff)"),
            ] = None,
            count: Annotated[int, Field(description="Results to return (1–50)", ge=1, le=50)] = 20,
            country: Annotated[S.CountryCode, Field(description="Country code")] = "US",
            search_lang: Annotated[S.SearchLang, Field(description="Search language")] = "en",
            ui_lang: Annotated[S.UiLang, Field(description="UI language")] = "en-US",
            units: Annotated[Optional[S.Units], Field(description="Measurement units")] = None,
            safesearch: Annotated[S.SafeSearch, Field(description="Safe-search level")] = "moderate",
            spellcheck: Annotated[bool, Field(description="Spellcheck the query")] = True,
        ) -> list[TextContent]:
            response = await svc.issue_request(
                "placeSearch",
                {
                    "q": query,
                    "location": location,
                    "latitude": latitude,
                    "longitude": longitude,
                    "radius": radius,
                    "count": count,
                    "country": country,
                    "search_lang": search_lang,
                    "ui_lang": ui_lang,
                    "units": units,
                    "safesearch": safesearch,
                    "spellcheck": spellcheck,
                },
            )
            results = response.get("results", [])
            if not results:
                raise ValueError("No place results found")
            pois: list[dict] = results
            return [
                TextContent(type="text", text=stringify(S.fmt_poi(p, {})))
                for p in pois
            ]

    # ── brave_summarizer ──────────────────────────────────────────────────────
    if settings.is_tool_permitted("brave_summarizer"):

        @server.tool(
            description=(
                "Retrieves an AI-generated summary of web search results using "
                "Brave's Summarizer API.\n\n"
                "Workflow: call brave_web_search with summary=true first, then pass "
                "the returned summarizer_key to this tool.\n\n"
                "Requires a Brave Search API Pro AI subscription."
            ),
            annotations=ToolAnnotations(title="Brave Summarizer", openWorldHint=True),
        )
        async def brave_summarizer(
            key: Annotated[str, Field(description="Summarizer key from brave_web_search called with summary=true")],
            entity_info: Annotated[bool, Field(description="Include related entity information")] = False,
        ) -> list[TextContent]:
            # Poll until summary is ready — mirrors pollForSummary() in summarizer/index.ts
            data: dict = {}
            for _ in range(_MAX_POLLS):
                data = await svc.issue_request(
                    "summarizer",
                    {"key": key, "entity_info": str(entity_info).lower()},
                )
                if data.get("status") != "incomplete" and data.get("summary"):
                    break
                await asyncio.sleep(_POLL_INTERVAL)
            else:
                raise RuntimeError("Summary generation timed out")

            summary_items = data.get("summary", [])
            text = S.fmt_summary_text(summary_items) if isinstance(summary_items, list) else str(summary_items)

            if not text:
                raise ValueError("No summary content returned")

            return [TextContent(type="text", text=text)]

    # ── brave_llm_context ─────────────────────────────────────────────────────
    if settings.is_tool_permitted("brave_llm_context"):

        @server.tool(
            description=(
                "Retrieves pre-extracted, relevance-ranked web content using Brave's LLM "
                "Context API, optimised for AI agents, LLM grounding, and RAG pipelines.\n\n"
                "Unlike a web search (links + short descriptions), this tool returns the "
                "actual substance of matching pages — text chunks, tables, code blocks — "
                "so the model can reason over it directly.\n\n"
                "When to use:\n"
                "  - Grounding answers in fresh, relevant web content (RAG)\n"
                "  - Question answering and fact-checking against current sources\n"
                "  - Gathering source material without manually fetching pages\n\n"
                "When relaying results in markdown environments, cite source URLs from the 'sources' map."
            ),
            annotations=ToolAnnotations(title="Brave LLM Context", openWorldHint=True),
        )
        async def brave_llm_context(
            query: Annotated[str, Field(description="Search query (max 400 chars, 50 words)")],
            country: Annotated[S.CountryCode, Field(description="Country for results")] = "US",
            search_lang: Annotated[S.SearchLang, Field(description="Search language")] = "en",
            count: Annotated[int, Field(description="Number of results to consider (1–50)", ge=1, le=50)] = 20,
            freshness: Annotated[
                Optional[str],
                Field(description="Time filter: pd pw pm py or YYYY-MM-DDtoYYYY-MM-DD"),
            ] = None,
            spellcheck: Annotated[bool, Field(description="Spellcheck the query")] = True,
            maximum_number_of_urls: Annotated[
                Optional[int],
                Field(description="Max URLs to extract content from (1–50)", ge=1, le=50),
            ] = None,
            maximum_number_of_tokens: Annotated[
                Optional[int],
                Field(description="Total token budget (1024–32768)", ge=1024, le=32768),
            ] = None,
            maximum_number_of_snippets: Annotated[
                Optional[int],
                Field(description="Max snippets across all URLs (1–256)", ge=1, le=256),
            ] = None,
            context_threshold_mode: Annotated[
                Optional[S.ContextThresholdMode],
                Field(description="Relevance filtering mode"),
            ] = None,
            maximum_number_of_tokens_per_url: Annotated[
                Optional[int],
                Field(description="Per-URL token budget (512–8192)", ge=512, le=8192),
            ] = None,
            maximum_number_of_snippets_per_url: Annotated[
                Optional[int],
                Field(description="Per-URL snippet cap (1–100)", ge=1, le=100),
            ] = None,
            enable_local: Annotated[Optional[bool], Field(description="Enable local recall")] = None,
            enable_source_metadata: Annotated[Optional[bool], Field(description="Enrich source metadata")] = None,
            # Geolocation headers
            x_loc_lat: Annotated[
                Optional[float],
                Field(description="User latitude (-90 to 90)", ge=-90, le=90),
            ] = None,
            x_loc_long: Annotated[
                Optional[float],
                Field(description="User longitude (-180 to 180)", ge=-180, le=180),
            ] = None,
            x_loc_city: Annotated[Optional[str], Field(description="User city")] = None,
            x_loc_country: Annotated[Optional[str], Field(description="User 2-letter country code")] = None,
        ) -> list[TextContent]:
            # Build optional geolocation headers — mirrors RequestHeadersSchema
            extra_headers: dict[str, str] = {}
            if x_loc_lat is not None:
                extra_headers["x-loc-lat"] = str(x_loc_lat)
            if x_loc_long is not None:
                extra_headers["x-loc-long"] = str(x_loc_long)
            if x_loc_city:
                extra_headers["x-loc-city"] = x_loc_city
            if x_loc_country:
                extra_headers["x-loc-country"] = x_loc_country

            response = await svc.issue_request(
                "llmContext",
                {
                    "q": query,
                    "country": country,
                    "search_lang": search_lang,
                    "count": count,
                    "freshness": freshness,
                    "spellcheck": spellcheck,
                    "maximum_number_of_urls": maximum_number_of_urls,
                    "maximum_number_of_tokens": maximum_number_of_tokens,
                    "maximum_number_of_snippets": maximum_number_of_snippets,
                    "context_threshold_mode": context_threshold_mode,
                    "maximum_number_of_tokens_per_url": maximum_number_of_tokens_per_url,
                    "maximum_number_of_snippets_per_url": maximum_number_of_snippets_per_url,
                    "enable_local": enable_local,
                    "enable_source_metadata": enable_source_metadata,
                },
                headers=extra_headers or None,
            )

            return [TextContent(type="text", text=stringify(response))]
