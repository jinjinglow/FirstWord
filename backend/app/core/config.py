from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FirstWord"
    app_db_path: Path = Path("local-data/app.db")
    temp_dir: Path = Path("local-data/tmp")
    whisper_model_size: str = "medium"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:7b-instruct"
    ollama_num_ctx: int = 4096
    ollama_num_predict: int = 1200
    ollama_timeout_seconds: int = 300

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def database_url(self) -> str:
        self.app_db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{self.app_db_path.as_posix()}"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.temp_dir.mkdir(parents=True, exist_ok=True)
    return settings
