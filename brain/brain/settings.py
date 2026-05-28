from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BRAIN_",
        env_file=None,
        case_sensitive=False,
        extra="ignore",
    )

    api_token: str
    vault_path: str = "/data/vault"
    events_path: str = "/data/events"
    redis_url: str = "redis://redis:6379/2"
    user_id: str = "erik"
    git_remote: str | None = None


def get_settings() -> Settings:
    return Settings()
