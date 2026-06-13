"""Centralized configuration — all secrets from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mcp_server_host: str = Field(default="0.0.0.0", alias="MCP_SERVER_HOST")
    mcp_server_port: int = Field(default=8080, alias="MCP_SERVER_PORT")

    azure_tenant_id: str | None = Field(default=None, alias="AZURE_TENANT_ID")
    azure_client_id: str | None = Field(default=None, alias="AZURE_CLIENT_ID")
    azure_client_secret: str | None = Field(default=None, alias="AZURE_CLIENT_SECRET")
    azure_api_audience: str | None = Field(default=None, alias="AZURE_API_AUDIENCE")

    fabric_workspace_id: str | None = Field(default=None, alias="FABRIC_WORKSPACE_ID")
    fabric_semantic_model_id: str | None = Field(default=None, alias="FABRIC_SEMANTIC_MODEL_ID")
    fabric_iq_project_connection_id: str | None = Field(
        default=None, alias="FABRIC_IQ_PROJECT_CONNECTION_ID"
    )
    fabric_api_base_url: str = Field(
        default="https://api.fabric.microsoft.com/v1", alias="FABRIC_API_BASE_URL"
    )
    fabric_iq_mcp_url: str | None = Field(default=None, alias="FABRIC_IQ_MCP_URL")

    use_mock_fabric_data: bool = Field(default=True, alias="USE_MOCK_FABRIC_DATA")

    @property
    def oauth_configured(self) -> bool:
        return bool(self.azure_tenant_id and azure_client_present(self))


def azure_client_present(settings: Settings) -> bool:
    return bool(settings.azure_client_id)


@lru_cache
def get_settings() -> Settings:
    return Settings()
