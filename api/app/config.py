"""App configuration via environment variables (.env)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "medfaq"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    embedding_model: str = "BAAI/bge-m3"
    retrieval_top_k: int = 3
    confidence_threshold: float = 0.55

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
