"""App configuration via environment variables (.env)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "medfaq"
    # BM25 lexical retrieval (no neural model, no AI).
    bm25_min_score: float = 1.0
    retrieval_top_k: int = 3

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
