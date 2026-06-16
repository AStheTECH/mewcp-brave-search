"""Constants: API base URL, timeouts, endpoint map, available tools."""

BRAVE_API_BASE = "https://api.search.brave.com"
API_TIMEOUT = 30

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
    # brave_local_search fires 3 HTTP requests per tool call (web + pois + descriptions);
    # set to 3 so a single tool invocation never self-trips the limiter.
    "per_second": 3,
    "per_month": 15000,
}

AVAILABLE_TOOLS: tuple[str, ...] = (
    "brave_web_search",
    "brave_local_search",
    "brave_video_search",
    "brave_image_search",
    "brave_news_search",
    "brave_place_search",
    "brave_summarizer",
    "brave_llm_context",
)
