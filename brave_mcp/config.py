"""Constants: API base URL, timeouts, endpoint map, available tools."""

import logging
import os

SERVER_VERSION = "v1.0.0"
BREAKING_CHANGES: list[dict] = []

BRAVE_API_BASE = "https://api.search.brave.com"

CONNECT_TIMEOUT = 5    # TCP connection — fixed across all servers
READ_TIMEOUT = 30      # Brave Search API has no documented SLA; 30s matches prior single-value timeout


def configure_logging() -> None:
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    try:
        from pythonjsonlogger import jsonlogger
        handler = logging.StreamHandler()
        handler.setFormatter(
            jsonlogger.JsonFormatter(fmt="%(asctime)s %(name)s %(levelname)s %(message)s")
        )
    except ImportError:
        handler = logging.StreamHandler()
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level)

# Matches typeToPathMap in BraveAPI/index.ts
ENDPOINT_MAP: dict[str, str] = {
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

RATE_LIMIT = {
    # search_local fires 3 HTTP requests per tool call (web + pois + descriptions);
    # set to 3 so a single tool invocation never self-trips the limiter.
    "per_second": 3,
    "per_month": 15000,
}

AVAILABLE_TOOLS: tuple[str, ...] = (
    "search_web",
    "search_local",
    "search_videos",
    "search_images",
    "search_news",
    "search_places",
    "summarize_search_results",
    "get_llm_context",
)
