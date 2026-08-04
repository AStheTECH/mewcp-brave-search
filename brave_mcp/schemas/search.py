"""Search group schemas: Brave Search API type contracts and Data/Result models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from ._base import ToolResult

# ── country codes (matches web/params.ts) ─────────────────────────────────────
CountryCode = Literal[
    "ALL", "AR", "AU", "AT", "BE", "BR", "CA", "CL", "DK", "FI",
    "FR", "DE", "HK", "IN", "ID", "IT", "JP", "KR", "MY", "MX",
    "NL", "NZ", "NO", "CN", "PL", "PT", "PH", "RU", "SA", "ZA",
    "ES", "SE", "CH", "TW", "TR", "GB", "US",
]

# ── search language codes ──────────────────────────────────────────────────────
SearchLang = Literal[
    "ar", "eu", "bn", "bg", "ca", "zh-hans", "zh-hant", "hr", "cs", "da",
    "nl", "en", "en-gb", "et", "fi", "fr", "gl", "de", "gu", "he",
    "hi", "hu", "is", "it", "jp", "kn", "ko", "lv", "lt", "ms",
    "ml", "mr", "nb", "pl", "pt-br", "pt-pt", "pa", "ro", "ru", "sr",
    "sk", "sl", "es", "sv", "ta", "te", "th", "tr", "uk", "vi",
]

# ── UI language codes ──────────────────────────────────────────────────────────
UiLang = Literal[
    "es-AR", "en-AU", "de-AT", "nl-BE", "fr-BE", "pt-BR", "en-CA", "fr-CA",
    "es-CL", "da-DK", "fi-FI", "fr-FR", "de-DE", "zh-HK", "en-IN", "en-ID",
    "it-IT", "ja-JP", "ko-KR", "en-MY", "es-MX", "nl-NL", "en-NZ", "no-NO",
    "zh-CN", "pl-PL", "en-PH", "ru-RU", "en-ZA", "es-ES", "sv-SE", "fr-CH",
    "de-CH", "zh-TW", "tr-TR", "en-GB", "en-US", "es-US",
]

# ── other shared enums ─────────────────────────────────────────────────────────
SafeSearch = Literal["off", "moderate", "strict"]
Units = Literal["metric", "imperial"]

ResultFilter = Literal[
    "discussions", "faq", "infobox", "news", "query",
    "summarizer", "videos", "web", "locations", "rich",
]

ContextThresholdMode = Literal["disabled", "strict", "lenient", "balanced"]


# ── search_web ────────────────────────────────────────────────────────

class WebSearchEntryData(BaseModel):
    model_config = ConfigDict(extra="allow")
    # every field below is optional since entries are heterogeneous by design
    summarizer_key: str | None = None
    url: str | None = None
    title: str | None = None
    description: str | None = None
    extra_snippets: list[str] | None = None
    question: str | None = None
    answer: str | None = None
    mutated_by_goggles: bool | None = None
    data: str | None = None  # discussion body
    source: dict[str, Any] | None = None
    breaking: bool | None = None
    is_live: bool | None = None
    age: str | None = None
    thumbnail_url: str | None = None
    duration: str | None = None
    view_count: int | None = None
    creator: str | None = None
    publisher: str | None = None
    tags: list[str] | None = None


class WebSearchData(BaseModel):
    model_config = ConfigDict(extra="allow")
    results: list[WebSearchEntryData]


class WebSearchResult(ToolResult):
    data: WebSearchData | None = None


# ── search_local ──────────────────────────────────────────────────────

class LocalResultEntryData(BaseModel):
    model_config = ConfigDict(extra="allow")
    # POI-shaped fields (from _fmt_poi)
    name: str | None = None
    address: str | None = None
    phone: str | None = None
    rating: float | None = None
    review_count: int | None = None
    hours: list[Any] | None = None
    price_range: str | None = None
    categories: list[str] | None = None
    url: str | None = None
    description: str | None = None
    # fallback web-result-shaped fields
    title: str | None = None
    extra_snippets: list[str] | None = None


class LocalSearchData(BaseModel):
    model_config = ConfigDict(extra="allow")
    results: list[LocalResultEntryData]


class LocalSearchResult(ToolResult):
    data: LocalSearchData | None = None


# ── search_videos ──────────────────────────────────────────────────────

class VideoResultItemData(BaseModel):
    model_config = ConfigDict(extra="allow")
    url: str | None = None
    title: str | None = None
    description: str | None = None
    age: str | None = None
    thumbnail_url: str | None = None
    duration: str | None = None
    view_count: int | None = None
    creator: str | None = None
    publisher: str | None = None
    tags: list[str] | None = None
    mutated_by_goggles: bool | None = None


class VideoSearchData(BaseModel):
    model_config = ConfigDict(extra="allow")
    results: list[VideoResultItemData]


class VideoSearchResult(ToolResult):
    data: VideoSearchData | None = None


# ── search_images ──────────────────────────────────────────────────────

class ImageResultItemData(BaseModel):
    model_config = ConfigDict(extra="allow")
    url: str | None = None
    source: str | None = None
    title: str | None = None
    width: int | None = None
    height: int | None = None
    format: str | None = None


class ImageSearchData(BaseModel):
    model_config = ConfigDict(extra="allow")
    results: list[ImageResultItemData]


class ImageSearchResult(ToolResult):
    data: ImageSearchData | None = None


# ── search_news ───────────────────────────────────────────────────────

class NewsResultItemData(BaseModel):
    model_config = ConfigDict(extra="allow")
    mutated_by_goggles: bool | None = None
    source: dict[str, Any] | None = None
    breaking: bool | None = None
    is_live: bool | None = None
    age: str | None = None
    url: str | None = None
    title: str | None = None
    description: str | None = None
    extra_snippets: list[str] | None = None


class NewsSearchData(BaseModel):
    model_config = ConfigDict(extra="allow")
    results: list[NewsResultItemData]


class NewsSearchResult(ToolResult):
    data: NewsSearchData | None = None


# ── search_places ──────────────────────────────────────────────────────

class PlaceResultItemData(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str | None = None
    address: str | None = None
    phone: str | None = None
    rating: float | None = None
    review_count: int | None = None
    hours: list[Any] | None = None
    price_range: str | None = None
    categories: list[str] | None = None
    url: str | None = None
    description: str | None = None


class PlaceSearchData(BaseModel):
    model_config = ConfigDict(extra="allow")
    results: list[PlaceResultItemData]


class PlaceSearchResult(ToolResult):
    data: PlaceSearchData | None = None


# ── summarize_search_results ────────────────────────────────────────────────────────

class SummarizerData(BaseModel):
    model_config = ConfigDict(extra="allow")
    text: str


class SummarizerResult(ToolResult):
    data: SummarizerData | None = None


# ── get_llm_context ───────────────────────────────────────────────────────

class LlmContextData(BaseModel):
    model_config = ConfigDict(extra="allow")


class LlmContextResult(ToolResult):
    data: LlmContextData | None = None
