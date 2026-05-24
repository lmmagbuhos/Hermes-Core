from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./hermes.db"
    profile_dir: str = "profiles"
    minimax_api_key: str = ""
    minimax_base_url: str = "https://api.minimax.chat/v1"
    minimax_model: str = ""
    dtt_ai_shared_token: str = ""

    model_config = SettingsConfigDict(env_prefix="HERMES_", env_file=".env", extra="ignore")


def get_settings() -> Settings:
    return Settings()
