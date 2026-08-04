"""Search group: search_web, search_local, search_videos,
search_images, search_news, search_places, summarize_search_results,
get_llm_context — the LLM-facing contract for all 8 Brave Search API operations.

Rules followed here (per MewCP server architecture):
  - Rich Field() descriptions and constraints for every parameter.
  - No credential parameters, ever — this module never touches auth.
  - One consistent error style: every tool returns a typed XxxResult carrying
    a ToolError on failure instead of raising.
"""

from __future__ import annotations

import logging
from typing import Annotated, Optional

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .. import service
from ..logging_utils import ToolLogger
from ..schemas.search import (
    ContextThresholdMode,
    CountryCode,
    ImageResultItemData,
    ImageSearchData,
    ImageSearchResult,
    LlmContextData,
    LlmContextResult,
    LocalResultEntryData,
    LocalSearchData,
    LocalSearchResult,
    NewsResultItemData,
    NewsSearchData,
    NewsSearchResult,
    PlaceResultItemData,
    PlaceSearchData,
    PlaceSearchResult,
    ResultFilter,
    SafeSearch,
    SearchLang,
    SummarizerData,
    SummarizerResult,
    UiLang,
    Units,
    VideoResultItemData,
    VideoSearchData,
    VideoSearchResult,
    WebSearchData,
    WebSearchEntryData,
    WebSearchResult,
)
from ._helpers import _err, _handle_request_exc, _upstream_err

logger = logging.getLogger("brave-search-mcp.tools.search")


def register_search_tools(mcp: FastMCP) -> None:

    # ── search_web ──────────────────────────────────────────────────────
    @mcp.tool(
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
        annotations=ToolAnnotations(
            title="Brave Web Search",
            readOnlyHint=True,
            destructiveHint=False,
            openWorldHint=True,
        ),
    )
    async def search_web(
        query: Annotated[str, Field(description="Search query (max 400 chars, 50 words)")],
        country: Annotated[CountryCode, Field(description="Country for results")] = "US",
        search_lang: Annotated[SearchLang, Field(description="Search language")] = "en",
        ui_lang: Annotated[UiLang, Field(description="UI language")] = "en-US",
        count: Annotated[int, Field(description="Number of web results (1–20)", ge=1, le=20)] = 10,
        offset: Annotated[int, Field(description="Pagination offset (0–9)", ge=0, le=9)] = 0,
        safesearch: Annotated[SafeSearch, Field(description="Safe-search level")] = "moderate",
        freshness: Annotated[
            Optional[str],
            Field(description="Time filter: pd (day) pw (week) pm (month) py (year) or YYYY-MM-DDtoYYYY-MM-DD"),
        ] = None,
        text_decorations: Annotated[bool, Field(description="Include decoration markers in snippets")] = True,
        spellcheck: Annotated[bool, Field(description="Spellcheck the query")] = True,
        result_filter: Annotated[
            Optional[list[ResultFilter]],
            Field(description="Subset of result types to return (default ['web','query'])"),
        ] = None,
        goggles: Annotated[
            Optional[list[str]],
            Field(description="Goggle HTTPS URLs for custom re-ranking"),
        ] = None,
        units: Annotated[Optional[Units], Field(description="Measurement units")] = None,
        extra_snippets: Annotated[
            Optional[bool],
            Field(description="Up to 5 extra excerpts per result (Pro plan)"),
        ] = None,
        summary: Annotated[
            Optional[bool],
            Field(description="Return a summarizer_key to pass to summarize_search_results"),
        ] = None,
    ) -> WebSearchResult:
        tlog = ToolLogger(logger, "search_web")
        try:
            result = await service.web_search({
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
            })
            if "error" in result:
                return _err(WebSearchResult, tlog, "UPSTREAM_ERROR", result["error"], 502, retriable=True,
                            log_message="Brave API request failed")
            tlog.success()
            return WebSearchResult(
                success=True,
                statusCode=200,
                data=WebSearchData(results=[WebSearchEntryData(**entry) for entry in result["results"]]),
            )
        except Exception as exc:
            return _handle_request_exc(WebSearchResult, tlog, exc)

    # ── search_local ────────────────────────────────────────────────────
    @mcp.tool(
        description=(
            "Searches for local businesses and places via the Brave Search API. "
            "Returns ratings, addresses, phone numbers, hours, and AI descriptions.\n\n"
            "Access to enriched POI data requires a Brave Search API Pro plan; "
            "the tool gracefully falls back to web results if local data is unavailable."
        ),
        annotations=ToolAnnotations(
            title="Brave Local Search",
            readOnlyHint=True,
            destructiveHint=False,
            openWorldHint=True,
        ),
    )
    async def search_local(
        query: Annotated[str, Field(description="Local search query, e.g. 'pizza near downtown Chicago'")],
        count: Annotated[int, Field(description="Results to return (1–20)", ge=1, le=20)] = 5,
        country: Annotated[CountryCode, Field(description="Country code")] = "US",
    ) -> LocalSearchResult:
        tlog = ToolLogger(logger, "search_local")
        try:
            result = await service.local_search(query, count, country)
            if "error" in result:
                return _err(LocalSearchResult, tlog, "UPSTREAM_ERROR", result["error"], 502, retriable=True,
                            log_message="Brave API request failed")
            tlog.success()
            return LocalSearchResult(
                success=True,
                statusCode=200,
                data=LocalSearchData(results=[LocalResultEntryData(**entry) for entry in result["results"]]),
            )
        except Exception as exc:
            return _handle_request_exc(LocalSearchResult, tlog, exc)

    # ── search_videos ────────────────────────────────────────────────────
    @mcp.tool(
        description="Searches for videos via the Brave Search API. Returns titles, URLs, durations, view counts, creators, and thumbnails.",
        annotations=ToolAnnotations(
            title="Brave Video Search",
            readOnlyHint=True,
            destructiveHint=False,
            openWorldHint=True,
        ),
    )
    async def search_videos(
        query: Annotated[str, Field(description="Video search query (max 400 chars, 50 words)")],
        country: Annotated[CountryCode, Field(description="Country for results")] = "US",
        search_lang: Annotated[SearchLang, Field(description="Search language")] = "en",
        ui_lang: Annotated[UiLang, Field(description="UI language")] = "en-US",
        count: Annotated[int, Field(description="Results to return (1–20)", ge=1, le=20)] = 10,
        offset: Annotated[int, Field(description="Pagination offset (0–9)", ge=0, le=9)] = 0,
        safesearch: Annotated[SafeSearch, Field(description="Safe-search level")] = "moderate",
        freshness: Annotated[
            Optional[str],
            Field(description="Time filter: pd pw pm py or YYYY-MM-DDtoYYYY-MM-DD"),
        ] = None,
        spellcheck: Annotated[bool, Field(description="Spellcheck the query")] = True,
    ) -> VideoSearchResult:
        tlog = ToolLogger(logger, "search_videos")
        try:
            result = await service.video_search({
                "q": query,
                "country": country,
                "search_lang": search_lang,
                "ui_lang": ui_lang,
                "count": count,
                "offset": offset,
                "safesearch": safesearch,
                "freshness": freshness,
                "spellcheck": spellcheck,
            })
            if "error" in result:
                return _err(VideoSearchResult, tlog, "UPSTREAM_ERROR", result["error"], 502, retriable=True,
                            log_message="Brave API request failed")
            tlog.success()
            return VideoSearchResult(
                success=True,
                statusCode=200,
                data=VideoSearchData(results=[VideoResultItemData(**entry) for entry in result["results"]]),
            )
        except Exception as exc:
            return _handle_request_exc(VideoSearchResult, tlog, exc)

    # ── search_images ────────────────────────────────────────────────────
    @mcp.tool(
        description=(
            "Searches for images via the Brave Search API. "
            "Returns direct image URLs, source pages, and dimensions. "
            "Images are returned as URLs — no base64 encoding."
        ),
        annotations=ToolAnnotations(
            title="Brave Image Search",
            readOnlyHint=True,
            destructiveHint=False,
            openWorldHint=True,
        ),
    )
    async def search_images(
        query: Annotated[str, Field(description="Image search query (max 400 chars, 50 words)")],
        country: Annotated[CountryCode, Field(description="Country for results")] = "US",
        search_lang: Annotated[SearchLang, Field(description="Search language")] = "en",
        count: Annotated[int, Field(description="Results to return (1–20)", ge=1, le=20)] = 10,
        safesearch: Annotated[SafeSearch, Field(description="Safe-search level")] = "moderate",
        spellcheck: Annotated[bool, Field(description="Spellcheck the query")] = True,
    ) -> ImageSearchResult:
        tlog = ToolLogger(logger, "search_images")
        try:
            result = await service.image_search({
                "q": query,
                "country": country,
                "search_lang": search_lang,
                "count": count,
                "safesearch": safesearch,
                "spellcheck": spellcheck,
            })
            if "error" in result:
                return _err(ImageSearchResult, tlog, "UPSTREAM_ERROR", result["error"], 502, retriable=True,
                            log_message="Brave API request failed")
            tlog.success()
            return ImageSearchResult(
                success=True,
                statusCode=200,
                data=ImageSearchData(results=[ImageResultItemData(**entry) for entry in result["results"]]),
            )
        except Exception as exc:
            return _handle_request_exc(ImageSearchResult, tlog, exc)

    # ── search_news ─────────────────────────────────────────────────────
    @mcp.tool(
        description="Searches for current news articles via the Brave Search API. Returns headlines, sources, publication age, and descriptions.",
        annotations=ToolAnnotations(
            title="Brave News Search",
            readOnlyHint=True,
            destructiveHint=False,
            openWorldHint=True,
        ),
    )
    async def search_news(
        query: Annotated[str, Field(description="News search query (max 400 chars, 50 words)")],
        country: Annotated[CountryCode, Field(description="Country for results")] = "US",
        search_lang: Annotated[SearchLang, Field(description="Search language")] = "en",
        ui_lang: Annotated[UiLang, Field(description="UI language")] = "en-US",
        count: Annotated[int, Field(description="Results to return (1–20)", ge=1, le=20)] = 10,
        offset: Annotated[int, Field(description="Pagination offset (0–9)", ge=0, le=9)] = 0,
        safesearch: Annotated[SafeSearch, Field(description="Safe-search level")] = "moderate",
        freshness: Annotated[
            Optional[str],
            Field(description="Time filter: pd pw pm py or YYYY-MM-DDtoYYYY-MM-DD"),
        ] = None,
        extra_snippets: Annotated[
            Optional[bool],
            Field(description="Up to 5 extra excerpts per result (Pro plan)"),
        ] = None,
        spellcheck: Annotated[bool, Field(description="Spellcheck the query")] = True,
    ) -> NewsSearchResult:
        tlog = ToolLogger(logger, "search_news")
        try:
            result = await service.news_search({
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
            })
            if "error" in result:
                return _err(NewsSearchResult, tlog, "UPSTREAM_ERROR", result["error"], 502, retriable=True,
                            log_message="Brave API request failed")
            tlog.success()
            return NewsSearchResult(
                success=True,
                statusCode=200,
                data=NewsSearchData(results=[NewsResultItemData(**entry) for entry in result["results"]]),
            )
        except Exception as exc:
            return _handle_request_exc(NewsSearchResult, tlog, exc)

    # ── search_places ────────────────────────────────────────────────────
    @mcp.tool(
        description=(
            "Retrieves points of interest (POIs) with structured business data via "
            "Brave's dedicated place-search endpoint. Returns addresses, hours, "
            "ratings, categories, and contact info.\n\n"
            "Geographic context is required — provide latitude/longitude or a "
            "location string (e.g. 'san francisco ca united states').\n\n"
            "Access requires a Brave Search API Pro plan."
        ),
        annotations=ToolAnnotations(
            title="Brave Place Search",
            readOnlyHint=True,
            destructiveHint=False,
            openWorldHint=True,
        ),
    )
    async def search_places(
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
        country: Annotated[CountryCode, Field(description="Country code")] = "US",
        search_lang: Annotated[SearchLang, Field(description="Search language")] = "en",
        ui_lang: Annotated[UiLang, Field(description="UI language")] = "en-US",
        units: Annotated[Optional[Units], Field(description="Measurement units")] = None,
        safesearch: Annotated[SafeSearch, Field(description="Safe-search level")] = "moderate",
        spellcheck: Annotated[bool, Field(description="Spellcheck the query")] = True,
    ) -> PlaceSearchResult:
        tlog = ToolLogger(logger, "search_places")
        try:
            result = await service.place_search({
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
            })
            if "error" in result:
                return _err(PlaceSearchResult, tlog, "UPSTREAM_ERROR", result["error"], 502, retriable=True,
                            log_message="Brave API request failed")
            tlog.success()
            return PlaceSearchResult(
                success=True,
                statusCode=200,
                data=PlaceSearchData(results=[PlaceResultItemData(**entry) for entry in result["results"]]),
            )
        except Exception as exc:
            return _handle_request_exc(PlaceSearchResult, tlog, exc)

    # ── summarize_search_results ──────────────────────────────────────────────────────
    @mcp.tool(
        description=(
            "Retrieves an AI-generated summary of web search results using "
            "Brave's Summarizer API.\n\n"
            "Workflow: call search_web with summary=true first, then pass "
            "the returned summarizer_key to this tool.\n\n"
            "Requires a Brave Search API Pro AI subscription."
        ),
        annotations=ToolAnnotations(
            title="Brave Summarizer",
            readOnlyHint=True,
            destructiveHint=False,
            openWorldHint=True,
        ),
    )
    async def summarize_search_results(
        key: Annotated[str, Field(description="Summarizer key from search_web called with summary=true")],
        entity_info: Annotated[bool, Field(description="Include related entity information")] = False,
    ) -> SummarizerResult:
        tlog = ToolLogger(logger, "summarize_search_results")
        try:
            result = await service.summarize(key, entity_info)
            if "error" in result:
                return _err(SummarizerResult, tlog, "UPSTREAM_ERROR", result["error"], 502, retriable=True,
                            log_message="Brave API request failed")
            tlog.success()
            return SummarizerResult(success=True, statusCode=200, data=SummarizerData(text=result["text"]))
        except Exception as exc:
            return _handle_request_exc(SummarizerResult, tlog, exc)

    # ── get_llm_context ─────────────────────────────────────────────────────
    @mcp.tool(
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
        annotations=ToolAnnotations(
            title="Brave LLM Context",
            readOnlyHint=True,
            destructiveHint=False,
            openWorldHint=True,
        ),
    )
    async def get_llm_context(
        query: Annotated[str, Field(description="Search query (max 400 chars, 50 words)")],
        country: Annotated[CountryCode, Field(description="Country for results")] = "US",
        search_lang: Annotated[SearchLang, Field(description="Search language")] = "en",
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
            Optional[ContextThresholdMode],
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
    ) -> LlmContextResult:
        tlog = ToolLogger(logger, "get_llm_context")
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

        try:
            result = await service.llm_context(
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
                extra_headers or None,
            )
            if "error" in result:
                return _err(LlmContextResult, tlog, "UPSTREAM_ERROR", result["error"], 502, retriable=True,
                            log_message="Brave API request failed")
            tlog.success()
            return LlmContextResult(success=True, statusCode=200, data=LlmContextData(**result["data"]))
        except Exception as exc:
            return _handle_request_exc(LlmContextResult, tlog, exc)
