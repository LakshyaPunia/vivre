from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os


class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_service_key: str = ""
    openai_api_key: str = ""
    models_dir: str = "models"
    app_env: str = "development"
    cors_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def chatbot_enabled(self) -> bool:
        return bool(self.openai_api_key and not self.openai_api_key.startswith("sk-..."))

    @property
    def supabase_enabled(self) -> bool:
        return bool(
            self.supabase_url
            and self.supabase_service_key
            and "your-project-id" not in self.supabase_url
            and self.supabase_service_key != "your-service-role-key"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
