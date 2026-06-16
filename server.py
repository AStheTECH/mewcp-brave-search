from fastmcp import FastMCP
from fastmcp_credentials import CredentialMiddleware, HeaderCredentialBackend

from brave_mcp.cli import parse_args
from brave_mcp.tools import register_tools

backend = HeaderCredentialBackend()
mcp = FastMCP(
    "MewCP Brave Search MCP Server",
    middleware=[CredentialMiddleware(backend, "static")],
)
register_tools(mcp)

# Expose ASGI app for hosting platforms (Vercel, Cloud Run, etc.)
app = mcp.http_app(path="/mcp", transport="streamable-http", stateless_http=True)

if __name__ == "__main__":
    args = parse_args()
    run_kwargs = {}
    if args.transport:
        run_kwargs["transport"] = args.transport
    if args.host:
        run_kwargs["host"] = args.host
    if args.port:
        run_kwargs["port"] = args.port
    mcp.run(**run_kwargs)
