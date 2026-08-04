**Search the web, images, videos, news, and local places through Brave's independent index — plus AI summarization and RAG-ready context extraction.**

A Model Context Protocol (MCP) server that exposes the Brave Search API's search endpoints for web, local, video, image, news, and place search, along with AI summarization and LLM-context extraction.


## Overview

The Brave Search MCP Server provides:

- Comprehensive web search with rich metadata — results can include FAQ, Discussions, News, and Video items alongside standard web results
- Local business and points-of-interest (POI) search with ratings, addresses, phone numbers, hours, and AI descriptions, with a graceful fallback to web results when enriched local data isn't available
- Dedicated video, image, and news search endpoints
- A structured place-search endpoint for POI data anchored to a location or lat/long coordinates
- AI-generated summarization of web search results via Brave's Summarizer API
- Pre-extracted, relevance-ranked web content via Brave's LLM Context API — actual page substance (text chunks, tables, code blocks) rather than just links and snippets

Perfect for:

- AI agents that need general-purpose web search grounded in an independent search index
- Local business lookup and "near me" style assistants
- News monitoring and current-events tools
- Media search integrations (images, videos)
- RAG pipelines that need pre-extracted, relevance-ranked web content for grounding
- Quickly summarizing a set of search results into an AI-generated answer


## Tools


<details>
<summary><code>search_web</code> — General-purpose web search with rich metadata</summary>

Performs web searches using the Brave Search API and returns comprehensive search results with rich metadata.

When to use:
  - General web searches for information, facts, or current topics
  - Location-based queries (restaurants, businesses, points of interest)
  - News searches for recent events or breaking stories
  - Finding videos, discussions, or FAQ content

Returns a JSON list of web results with title, description, and URL. When result_filter is empty, results may also contain FAQ, Discussions, News, and Video items.

**Inputs:**
```
- `query` (string, required) — Search query (max 400 chars, 50 words)
- `country` (CountryCode, optional, default: "US") — Country for results
- `search_lang` (SearchLang, optional, default: "en") — Search language
- `ui_lang` (UiLang, optional, default: "en-US") — UI language
- `count` (int, optional, default: 10) — Number of web results (1–20)
- `offset` (int, optional, default: 0) — Pagination offset (0–9)
- `safesearch` (SafeSearch, optional, default: "moderate") — Safe-search level
- `freshness` (string, optional) — Time filter: pd (day) pw (week) pm (month) py (year) or YYYY-MM-DDtoYYYY-MM-DD
- `text_decorations` (bool, optional, default: true) — Include decoration markers in snippets
- `spellcheck` (bool, optional, default: true) — Spellcheck the query
- `result_filter` (list of ResultFilter, optional) — Subset of result types to return (default ['web','query'])
- `goggles` (list of string, optional) — Goggle HTTPS URLs for custom re-ranking
- `units` (Units, optional) — Measurement units
- `extra_snippets` (bool, optional) — Up to 5 extra excerpts per result (Pro plan)
- `summary` (bool, optional) — Return a summarizer_key to pass to summarize_search_results
```

**Output `data` schema:**

```typescript
{
  results: {
    summarizer_key: string | null;
    url: string | null;
    title: string | null;
    description: string | null;
    extra_snippets: string[] | null;
    question: string | null;
    answer: string | null;
    mutated_by_goggles: boolean | null;
    data: string | null;       // discussion body
    source: Record<string, unknown> | null;
    breaking: boolean | null;
    is_live: boolean | null;
    age: string | null;
    thumbnail_url: string | null;
    duration: string | null;
    view_count: number | null;
    creator: string | null;
    publisher: string | null;
    tags: string[] | null;
  }[];
}
```

</details>


<details>
<summary><code>search_local</code> — Local business and POI search</summary>

Searches for local businesses and places via the Brave Search API. Returns ratings, addresses, phone numbers, hours, and AI descriptions.

Access to enriched POI data requires a Brave Search API Pro plan; the tool gracefully falls back to web results if local data is unavailable.

**Inputs:**
```
- `query` (string, required) — Local search query, e.g. 'pizza near downtown Chicago'
- `count` (int, optional, default: 5) — Results to return (1–20)
- `country` (CountryCode, optional, default: "US") — Country code
```

**Output `data` schema:**

```typescript
{
  results: {
    // POI-shaped fields
    name: string | null;
    address: string | null;
    phone: string | null;
    rating: number | null;
    review_count: number | null;
    hours: unknown[] | null;
    price_range: string | null;
    categories: string[] | null;
    url: string | null;
    description: string | null;
    // fallback web-result-shaped fields (when local data is unavailable)
    title: string | null;
    extra_snippets: string[] | null;
  }[];
}
```

</details>


<details>
<summary><code>search_videos</code> — Video search</summary>

Searches for videos via the Brave Search API. Returns titles, URLs, durations, view counts, creators, and thumbnails.

**Inputs:**
```
- `query` (string, required) — Video search query (max 400 chars, 50 words)
- `country` (CountryCode, optional, default: "US") — Country for results
- `search_lang` (SearchLang, optional, default: "en") — Search language
- `ui_lang` (UiLang, optional, default: "en-US") — UI language
- `count` (int, optional, default: 10) — Results to return (1–20)
- `offset` (int, optional, default: 0) — Pagination offset (0–9)
- `safesearch` (SafeSearch, optional, default: "moderate") — Safe-search level
- `freshness` (string, optional) — Time filter: pd pw pm py or YYYY-MM-DDtoYYYY-MM-DD
- `spellcheck` (bool, optional, default: true) — Spellcheck the query
```

**Output `data` schema:**

```typescript
{
  results: {
    url: string | null;
    title: string | null;
    description: string | null;
    age: string | null;
    thumbnail_url: string | null;
    duration: string | null;
    view_count: number | null;
    creator: string | null;
    publisher: string | null;
    tags: string[] | null;
    mutated_by_goggles: boolean | null;
  }[];
}
```

</details>


<details>
<summary><code>search_images</code> — Image search</summary>

Searches for images via the Brave Search API. Returns direct image URLs, source pages, and dimensions. Images are returned as URLs — no base64 encoding.

**Inputs:**
```
- `query` (string, required) — Image search query (max 400 chars, 50 words)
- `country` (CountryCode, optional, default: "US") — Country for results
- `search_lang` (SearchLang, optional, default: "en") — Search language
- `count` (int, optional, default: 10) — Results to return (1–20)
- `safesearch` (SafeSearch, optional, default: "moderate") — Safe-search level
- `spellcheck` (bool, optional, default: true) — Spellcheck the query
```

**Output `data` schema:**

```typescript
{
  results: {
    url: string | null;
    source: string | null;
    title: string | null;
    width: number | null;
    height: number | null;
    format: string | null;
  }[];
}
```

</details>


<details>
<summary><code>search_news</code> — News search</summary>

Searches for current news articles via the Brave Search API. Returns headlines, sources, publication age, and descriptions.

**Inputs:**
```
- `query` (string, required) — News search query (max 400 chars, 50 words)
- `country` (CountryCode, optional, default: "US") — Country for results
- `search_lang` (SearchLang, optional, default: "en") — Search language
- `ui_lang` (UiLang, optional, default: "en-US") — UI language
- `count` (int, optional, default: 10) — Results to return (1–20)
- `offset` (int, optional, default: 0) — Pagination offset (0–9)
- `safesearch` (SafeSearch, optional, default: "moderate") — Safe-search level
- `freshness` (string, optional) — Time filter: pd pw pm py or YYYY-MM-DDtoYYYY-MM-DD
- `extra_snippets` (bool, optional) — Up to 5 extra excerpts per result (Pro plan)
- `spellcheck` (bool, optional, default: true) — Spellcheck the query
```

**Output `data` schema:**

```typescript
{
  results: {
    mutated_by_goggles: boolean | null;
    source: Record<string, unknown> | null;
    breaking: boolean | null;
    is_live: boolean | null;
    age: string | null;
    url: string | null;
    title: string | null;
    description: string | null;
    extra_snippets: string[] | null;
  }[];
}
```

</details>


<details>
<summary><code>search_places</code> — Structured POI / place search</summary>

Retrieves points of interest (POIs) with structured business data via Brave's dedicated place-search endpoint. Returns addresses, hours, ratings, categories, and contact info.

Geographic context is required — provide latitude/longitude or a location string (e.g. 'san francisco ca united states').

Access requires a Brave Search API Pro plan.

**Inputs:**
```
- `query` (string, required) — Search query — shapes result type, e.g. 'coffee shops' or 'Eiffel Tower'
- `location` (string, optional) — Location context, e.g. 'san francisco ca united states' or 'tokyo japan'
- `latitude` (float, optional) — Latitude (-90 to 90)
- `longitude` (float, optional) — Longitude (-180 to 180)
- `radius` (int, optional) — Proximity bias in metres (not a hard cutoff)
- `count` (int, optional, default: 20) — Results to return (1–50)
- `country` (CountryCode, optional, default: "US") — Country code
- `search_lang` (SearchLang, optional, default: "en") — Search language
- `ui_lang` (UiLang, optional, default: "en-US") — UI language
- `units` (Units, optional) — Measurement units
- `safesearch` (SafeSearch, optional, default: "moderate") — Safe-search level
- `spellcheck` (bool, optional, default: true) — Spellcheck the query
```

**Output `data` schema:**

```typescript
{
  results: {
    name: string | null;
    address: string | null;
    phone: string | null;
    rating: number | null;
    review_count: number | null;
    hours: unknown[] | null;
    price_range: string | null;
    categories: string[] | null;
    url: string | null;
    description: string | null;
  }[];
}
```

</details>


<details>
<summary><code>summarize_search_results</code> — AI summary of prior web search results</summary>

Retrieves an AI-generated summary of web search results using Brave's Summarizer API.

Workflow: call search_web with summary=true first, then pass the returned summarizer_key to this tool.

Requires a Brave Search API Pro AI subscription.

**Inputs:**
```
- `key` (string, required) — Summarizer key from search_web called with summary=true
- `entity_info` (bool, optional, default: false) — Include related entity information
```

**Output `data` schema:**

```typescript
{
  text: string;
}
```

</details>


<details>
<summary><code>get_llm_context</code> — Relevance-ranked web content for RAG/grounding</summary>

Retrieves pre-extracted, relevance-ranked web content using Brave's LLM Context API, optimised for AI agents, LLM grounding, and RAG pipelines.

Unlike a web search (links + short descriptions), this tool returns the actual substance of matching pages — text chunks, tables, code blocks — so the model can reason over it directly.

When to use:
  - Grounding answers in fresh, relevant web content (RAG)
  - Question answering and fact-checking against current sources
  - Gathering source material without manually fetching pages

When relaying results in markdown environments, cite source URLs from the 'sources' map.

**Inputs:**
```
- `query` (string, required) — Search query (max 400 chars, 50 words)
- `country` (CountryCode, optional, default: "US") — Country for results
- `search_lang` (SearchLang, optional, default: "en") — Search language
- `count` (int, optional, default: 20) — Number of results to consider (1–50)
- `freshness` (string, optional) — Time filter: pd pw pm py or YYYY-MM-DDtoYYYY-MM-DD
- `spellcheck` (bool, optional, default: true) — Spellcheck the query
- `maximum_number_of_urls` (int, optional) — Max URLs to extract content from (1–50)
- `maximum_number_of_tokens` (int, optional) — Total token budget (1024–32768)
- `maximum_number_of_snippets` (int, optional) — Max snippets across all URLs (1–256)
- `context_threshold_mode` (ContextThresholdMode, optional) — Relevance filtering mode
- `maximum_number_of_tokens_per_url` (int, optional) — Per-URL token budget (512–8192)
- `maximum_number_of_snippets_per_url` (int, optional) — Per-URL snippet cap (1–100)
- `enable_local` (bool, optional) — Enable local recall
- `enable_source_metadata` (bool, optional) — Enrich source metadata
- `x_loc_lat` (float, optional) — User latitude (-90 to 90)
- `x_loc_long` (float, optional) — User longitude (-180 to 180)
- `x_loc_city` (string, optional) — User city
- `x_loc_country` (string, optional) — User 2-letter country code
```

**Output `data` schema:**

```typescript
{
  // This model declares no fixed fields of its own — the entire response
  // shape is the passthrough JSON from Brave's LLM Context API. The tool
  // description references a `sources` map for citing result URLs.
  [key: string]: unknown;
}
```

</details>


## API Parameters Reference

<details>
<summary><strong>Response Envelope</strong></summary>

Every tool returns the same top-level envelope. Only `data` varies per tool.

```json
// Success
{
  "success": true,
  "statusCode": 200,
  "retriable": false,
  "retry_after_seconds": null,
  "error": null,
  "data": { ... }
}

// Error
{
  "success": false,
  "statusCode": 400,
  "retriable": false,
  "retry_after_seconds": null,
  "error": { "code": "{ERROR_CODE}", "message": "{description}", "details": {} },
  "data": null
}
```

- `retriable` — `true` when it is safe to retry (rate limit, network error, 503). `false` for validation and auth errors.
- `retry_after_seconds` — seconds to wait before retrying; present only when `retriable` is `true` and the upstream specifies a delay.
- `error.code` — machine-readable string: `VALIDATION_ERROR`, `AUTH_ERROR`, `UPSTREAM_ERROR`, `SERVER_ERROR`.
- All `data` models accept additional, undocumented fields beyond what's listed above (`extra="allow"`) — Brave may add fields to its API responses that aren't reflected in these schemas yet.

</details>

<details>
<summary><strong>Common Parameters</strong></summary>

These appear, with the same meaning, across most of the search tools:

- `country` (CountryCode) — "Country for results" (`search_local` and `search_places` phrase this as "Country code")
- `search_lang` (SearchLang) — Search language
- `ui_lang` (UiLang) — UI language
- `safesearch` (SafeSearch: `off` | `moderate` | `strict`) — Safe-search level
- `spellcheck` (bool) — Spellcheck the query
- `freshness` (string) — Time filter: `pd` (day) / `pw` (week) / `pm` (month) / `py` (year), or a custom `YYYY-MM-DDtoYYYY-MM-DD` range
- `units` (Units: `metric` | `imperial`) — Measurement units

`CountryCode`, `SearchLang`, and `UiLang` are each closed lists of ISO-style codes matching Brave's supported values — pass one of the enumerated codes for the given parameter.

</details>


## Getting Your Brave Search API Key

<details>
<summary><strong>Steps</strong></summary>

1. Go to the [Brave Search API dashboard](https://api-dashboard.search.brave.com/)
2. Sign up or log in, then subscribe to a plan (a free tier is available)
3. Open the API Keys section of the dashboard and create a new key (or use the one generated for you on signup)
4. Copy the generated key — you will only see it once

</details>


## Troubleshooting

<details>
<summary><strong>Missing or Invalid Headers</strong></summary>

- **Cause:** API key not provided in request headers or incorrect format
- **Solution:**
  1. Verify `Authorization: Bearer YOUR_API_KEY` and `X-Mewcp-Credential-Id: CREDENTIAL-ID` headers are present
  2. Check API key is active in your MewCP account

</details>

<details>
<summary><strong>Insufficient Credits</strong></summary>

- **Cause:** API calls have exceeded your request limits
- **Solution:**
  1. Check credit usage in your Curious Layer dashboard
  2. Upgrade to a paid plan or add credits for higher limits
  3. Contact support for credit adjustments

</details>

<details>
<summary><strong>Credential Not Connected</strong></summary>

- **Cause:** No Brave Search credential linked to your account
- **Solution:**
  1. Go to **Credentials** in your MewCP dashboard
  2. Connect your Brave Search account (OAuth) or add your API key (static)
  3. Retry the request with the correct `X-Mewcp-Credential-Id` header

</details>

<details>
<summary><strong>Malformed Request Payload</strong></summary>

- **Cause:** JSON payload is invalid or missing required fields
- **Solution:**
  1. Validate JSON syntax before sending
  2. Ensure all required tool parameters are included
  3. Check parameter types match expected values

</details>

<details>
<summary><strong>Server Not Found</strong></summary>

- **Cause:** Incorrect server name in the API endpoint
- **Solution:**
  1. Verify endpoint format: `mewcp-brave-search/mcp/{tool-name}`
  2. Use correct server name from documentation
  3. Check available servers in your Curious Layer account

</details>

<details>
<summary><strong>Brave Search API Error</strong></summary>

- **Cause:** Upstream Brave Search API returned an error
- **Solution:**
  1. Check the Brave Search API's status page for ongoing incidents
  2. Verify your credential has the required permissions (some tools require a Pro plan)
  3. Review the error message for specific details

</details>

---

<details>
<summary><strong>Resources</strong></summary>

- **[Brave Search API Documentation](https://api-dashboard.search.brave.com/app/documentation)** — Official API reference
- **[FastMCP Docs](https://gofastmcp.com/v2/getting-started/welcome)** — FastMCP specification
- **[FastMCP Credentials](https://pypi.org/project/fastmcp-credentials/)** — FastMCP Credentials package for credential handling

</details>
