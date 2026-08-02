"""Type contracts for tool inputs — Literal aliases mirroring Brave's Zod schemas."""

from __future__ import annotations

from typing import Literal

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
