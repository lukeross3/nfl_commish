from datetime import timedelta
from typing import Optional

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Settings values
    THE_ODDS_API_KEY: SecretStr
    GOOGLE_SHEETS_SECRET_PATH: Optional[str]
    copy_timedelta: timedelta = timedelta(minutes=5)
    scoring_timedelta: timedelta = timedelta(hours=5)
    max_weeks: int = 18

    # Settings config
    model_config = SettingsConfigDict(extra="ignore", env_file=".env")
