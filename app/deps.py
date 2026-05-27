import os
from functools import lru_cache
from pathlib import Path

from twscrape import API

DB_PATH = Path(os.environ.get("X_API_DB", Path(__file__).resolve().parents[1] / "x-api.db"))


@lru_cache
def get_api() -> API:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return API(str(DB_PATH))
