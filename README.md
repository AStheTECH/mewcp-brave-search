# MewCP Brave Search MCP Server

A stateless, multi-tenant [FastMCP](https://gofastmcp.com) server that wraps the
[Brave Search API](https://api.search.brave.com) as a set of MCP tools.

Built on the standard MewCP server architecture: credentials are never stored
on this server and never seen by the LLM — the MewCP Gateway resolves each
caller's stored Brave API key and injects it as an `X-Mcp-Cred-Fields` header
on every request, scoped to that one tool call.

## Tools

| Tool | Description |
|------|-------------|
| `brave_web_search` | General web search; may also surface FAQ, discussions, news, and video results |
| `brave_local_search` | Local businesses/places, with fallback to web results |
| `brave_video_search` | Video search |
| `brave_image_search` | Image search |
| `brave_news_search` | News search |
| `brave_place_search` | Structured POI data (Pro plan) |
| `brave_summarizer` | AI-generated summary of a prior web search (Pro AI plan) |
| `brave_llm_context` | Pre-extracted, relevance-ranked web content for RAG/grounding |

## Auth setup

This server uses `static` credentials. The MewCP Gateway stores your Brave
API key and injects it under the `api_key` field on every request:

```
X-Mcp-Cred-Fields: {"api_key": "<your-brave-api-key>"}
```

Get a key at https://api.search.brave.com/app/keys and connect it via the
MewCP credentials UI — this server never reads `.env` files or environment
variables for the key.

## Running locally

```bash
pip install -r requirements.txt
python server.py --transport streamable-http --port 8080
```

Without the gateway in front of it, you must set the credential header
yourself when calling a tool:

```bash
curl -X POST http://localhost:8080/mcp \
  -H 'Content-Type: application/json' \
  -H 'X-Mcp-Cred-Fields: {"api_key": "<real-brave-api-key>"}' \
  -d '<MCP JSON-RPC tools/call payload>'
```

A request without that header fails with a missing-credential error rather
than a crash or a silent fallback.

## Troubleshooting

- **`Missing 'api_key' credential field`** — the gateway didn't inject
  `X-Mcp-Cred-Fields`, or it didn't contain an `api_key` key. Reconnect the
  Brave credential in the MewCP UI, or check the header you're sending in
  local testing.
- **`Brave API 4xx/5xx: ...`** — the Brave API rejected the request; the
  error body from Brave is included verbatim.
- **`Rate limit exceeded`** — the in-process limiter tripped
  (`brave_mcp/config.py: RATE_LIMIT`); back off and retry.
