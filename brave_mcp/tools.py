"""
Register all 8 Brave Search tools — the LLM-facing contract.

Rules followed here (per MewCP server architecture):
  - Rich Field() descriptions and constraints for every parameter.
  - No credential parameters, ever — tools.py never touches auth.
  - One consistent error style: every tool returns a single TextContent
    carrying {"error": "..."} on failure instead of raising.
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastmcp import FastMCP
from mcp.types import TextContent, ToolAnnotations
from pydantic import Field

from . import schemas as S
from . import service
from .utils import stringify


def _error(message: str) -> list[TextContent]:
    return [TextContent(type="text", text=stringify({"error": message}))]


def register_tools(mcp: FastMCP) -> None:

    # ── brave_web_search ──────────────────────────────────────────────────────
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
            return _error(result["error"])
        return [TextContent(type="text", text=stringify(entry)) for entry in result["results"]]

    # ── brave_local_search ────────────────────────────────────────────────────
    @mcp.tool(
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
        result = await service.local_search(query, count, country)
        if "error" in result:
            return _error(result["error"])
        return [TextContent(type="text", text=stringify(entry)) for entry in result["results"]]

    # ── brave_video_search ────────────────────────────────────────────────────
    @mcp.tool(
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
            return _error(result["error"])
        return [TextContent(type="text", text=stringify(entry)) for entry in result["results"]]

    # ── brave_image_search ────────────────────────────────────────────────────
    @mcp.tool(
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
        result = await service.image_search({
            "q": query,
            "country": country,
            "search_lang": search_lang,
            "count": count,
            "safesearch": safesearch,
            "spellcheck": spellcheck,
        })
        if "error" in result:
            return _error(result["error"])
        return [TextContent(type="text", text=stringify(entry)) for entry in result["results"]]

    # ── brave_news_search ─────────────────────────────────────────────────────
    @mcp.tool(
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
            return _error(result["error"])
        return [TextContent(type="text", text=stringify(entry)) for entry in result["results"]]

    # ── brave_place_search ────────────────────────────────────────────────────
    @mcp.tool(
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
            return _error(result["error"])
        return [TextContent(type="text", text=stringify(entry)) for entry in result["results"]]

    # ── brave_summarizer ──────────────────────────────────────────────────────
    @mcp.tool(
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
        result = await service.summarize(key, entity_info)
        if "error" in result:
            return _error(result["error"])
        return [TextContent(type="text", text=result["text"])]

    # ── brave_llm_context ─────────────────────────────────────────────────────
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
            return _error(result["error"])
        return [TextContent(type="text", text=stringify(result["data"]))]
