from pathlib import Path
from pydantic import BaseModel


class Settings(BaseModel):
    database_path: str = "data/agent_runtime.sqlite3"
    store_raw_payloads: bool = False


settings = Settings()


def ensure_data_dir() -> None:
    Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
