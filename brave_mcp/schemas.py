"""Enum type aliases mirroring Brave's Zod schemas, plus POI formatter."""

from __future__ import annotations

from typing import Any, Literal

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


# ── result formatters (return dicts for stringify()) ──────────────────────────

def fmt_web_results(web: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "url": r.get("url"),
            "title": r.get("title"),
            "description": r.get("description"),
            "extra_snippets": r.get("extra_snippets"),
        }
        for r in web.get("results", [])
    ]


def fmt_faq_results(faq: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "question": r.get("question"),
            "answer": r.get("answer"),
            "title": r.get("title"),
            "url": r.get("url"),
        }
        for r in faq.get("results", [])
    ]


def fmt_discussion_results(discussions: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "mutated_by_goggles": discussions.get("mutated_by_goggles"),
            "url": r.get("url"),
            "data": r.get("data"),
        }
        for r in discussions.get("results", [])
    ]


def fmt_news_results(news: dict[str, Any]) -> list[dict[str, Any]]:
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


def fmt_video_results(videos: dict[str, Any]) -> list[dict[str, Any]]:
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


def fmt_image_results(images: dict[str, Any]) -> list[dict[str, Any]]:
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


def fmt_poi(poi: dict[str, Any], desc_map: dict[str, list[str]]) -> dict[str, Any]:
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


def fmt_summary_text(summary_items: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for item in summary_items:
        t = item.get("type")
        if t == "token":
            parts.append(item.get("data", ""))
        elif t == "inlineLocation":
            parts.append(f"[{item.get('title', '')}]({item.get('url', '')})")
    return "".join(parts)
