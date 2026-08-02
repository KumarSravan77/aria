from __future__ import annotations
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    app_name: str = 'aria'
    app_env: str = 'local'  # local | test | production
    database_url: str = 'sqlite:///./incident_investigator.db'
    redis_url: str = 'redis://localhost:6379/0'
    event_bus_backend: str = 'inmemory'  # inmemory | redis

    # No hardcoded secret defaults. Use .env for local runs; scripts/bootstrap-env.sh can generate one.
    api_auth_token: str = Field(default='')
    alertmanager_webhook_secret: str = Field(default='')
    falco_webhook_secret: str = Field(default='')
    api_user_id: str = 'local-sre'
    api_user_role: str = 'sre'
    api_user_team: str = 'platform'
    # Optional comma-separated token map: token:user_id:role:team,token2:user2:role:team
    api_auth_tokens: str | None = None

    collaboration_provider: str = 'stdout'
    slack_bot_token: str | None = None
    slack_default_channel: str | None = None
    mattermost_url: str | None = None
    mattermost_token: str | None = None
    mattermost_team_id: str | None = None

    otel_enabled: bool = False
    otel_endpoint: str | None = None

    rebac_backend: str = 'local'  # local | openfga
    openfga_api_url: str | None = None
    openfga_store_id: str | None = None
    openfga_authorization_model_id: str | None = None
    openfga_token: str | None = None

    ollama_base_url: str = 'http://localhost:11434'
    ollama_model: str = 'llama3.1:8b'
    llm_enabled: bool = False

    argocd_api_url: str | None = None
    argocd_token: str | None = None
    prometheus_url: str = 'http://localhost:9090'
    loki_url: str = 'http://localhost:3100'
    tempo_url: str = 'http://localhost:3200'
    opencost_url: str = 'http://localhost:9003'

    chaos_enabled: bool = False
    chaos_default_namespace: str = 'demo'
    chaos_default_service: str = 'checkout-api'
    chaos_default_app_label: str = 'app=checkout-api'
    chaos_default_duration_seconds: int = 30
    chaos_validation_window_seconds: int = 300

    webhook_timestamp_tolerance_seconds: int = 300  # 5 minutes
    servicenow_url: str | None = None
    servicenow_token: str | None = None

    confluence_base_url: str | None = None
    confluence_email: str | None = None
    confluence_api_token: str | None = None

    @field_validator('api_auth_token', 'alertmanager_webhook_secret', 'falco_webhook_secret')
    @classmethod
    def require_explicit_secret(cls, value: str, info):
        # Keep import-time validation lightweight for tests, but fail closed for real environments.
        # Local bootstrap writes .env automatically; production must inject real secrets.
        if not value:
            raise ValueError(f'{info.field_name} must be set. Run scripts/bootstrap-env.sh for local dev or inject it via secrets manager.')
        if value in {'dev-token', 'dev-alertmanager-secret', 'dev-falco-secret'}:
            raise ValueError(f'{info.field_name} uses an unsafe sample value. Generate a unique local secret.')
        return value

settings = Settings()
