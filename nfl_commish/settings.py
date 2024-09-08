from datetime import timedelta
from typing import Optional

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Settings values
    the_odds_api_key: SecretStr
    google_sheets_secret_path: Optional[str]
    copy_timedelta: timedelta = timedelta(minutes=5)
    scoring_timedelta: timedelta = timedelta(hours=5)
    max_weeks: int = 18
    missed_pred_str: str = "missed"

    # Settings config
    model_config = SettingsConfigDict(extra="ignore", env_file=".env")
