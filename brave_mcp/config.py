from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

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


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
    )

    api_key: str = Field("", alias="BRAVE_API_KEY")
    transport: Literal["stdio", "http"] = Field("stdio", alias="BRAVE_MCP_TRANSPORT")
    port: int = Field(8080, alias="BRAVE_MCP_PORT", ge=1, le=65535)
    host: str = Field("0.0.0.0", alias="BRAVE_MCP_HOST")
    log_level: Literal["debug", "info", "warning", "error"] = Field(
        "info", alias="BRAVE_MCP_LOG_LEVEL"
    )
    enabled_tools: list[str] = Field(default_factory=list, alias="BRAVE_MCP_ENABLED_TOOLS")
    disabled_tools: list[str] = Field(default_factory=list, alias="BRAVE_MCP_DISABLED_TOOLS")
    stateless: bool = Field(False, alias="BRAVE_MCP_STATELESS")

    @field_validator("enabled_tools", "disabled_tools", mode="before")
    @classmethod
    def _split(cls, v: object) -> list[str]:
        if isinstance(v, str):
            return [t.strip() for t in v.split() if t.strip()]
        return list(v) if v else []

    @model_validator(mode="after")
    def _validate(self) -> Settings:
        if not self.api_key:
            raise ValueError(
                "BRAVE_API_KEY is required. "
                "Get your key at https://api.search.brave.com/app/keys "
                "then set it in .env or as an environment variable."
            )
        if self.enabled_tools and self.disabled_tools:
            raise ValueError(
                "Cannot use BRAVE_MCP_ENABLED_TOOLS and BRAVE_MCP_DISABLED_TOOLS simultaneously"
            )
        unknown = set(self.enabled_tools + self.disabled_tools) - set(AVAILABLE_TOOLS)
        if unknown:
            raise ValueError(
                f"Unknown tool(s): {', '.join(sorted(unknown))}. "
                f"Available: {', '.join(AVAILABLE_TOOLS)}"
            )
        if self.transport == "http" and not self.host:
            raise ValueError("BRAVE_MCP_HOST is required when using HTTP transport")
        return self

    def is_tool_permitted(self, name: str) -> bool:
        if self.enabled_tools:
            return name in self.enabled_tools
        if self.disabled_tools:
            return name not in self.disabled_tools
        return True
