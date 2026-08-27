from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://netra:netra@localhost:5433/netra"

    jwt_secret: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    ai_gateway_base_url: str = "https://ai.tcetcercd.in/v1"
    ai_gateway_api_key: str = ""
    ai_gateway_model: str = "/home/user1/models/Qwen3.6-35B-A3B-NVFP4-Fast"
    llm_enabled: bool = True
    llm_timeout_seconds: float = 2.5
    llm_max_retries: int = 1
    llm_concurrency: int = 4

    simulation_seed: int = 42
    priority_rules_version: str = "priority-v1.0"
    nlp_rules_version: str = "rules-v1"

    rate_limit_enabled: bool = True
    load_test_mode: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()