import argparse
from datetime import datetime
from typing import Optional

import gspread as gs

# import pandas as pd
from loguru import logger
from pydantic import BaseModel, ConfigDict
from pytz import timezone

# from nfl_commish.game import (
#     get_the_odds_json,
#     get_this_weeks_games,
#     parse_the_odds_json,
# )
from nfl_commish.settings import Settings
from nfl_commish.utils import read_config


class ScriptParams(BaseModel):
    week: int  # Week number to initialize
    secret_path: Optional[str] = None  # Directory containing google sheets secret
    gspread_username: str = "lukeross"  # Username for google sheets account
    sheet_name: str = "Luke NFL Confidence '24-'25"  # Sheet name under the account

    model_config = ConfigDict(extra="forbid")


def main(config):

    # Get the google sheets secret
    settings = Settings()
    if config.secret_path is not None:
        secret_path = config.secret_path
    elif settings.GOOGLE_SHEETS_SECRET_PATH is not None:
        secret_path = settings.GOOGLE_SHEETS_SECRET_PATH
    else:
        logger.error(
            "No google sheets path provided. Must pass '--secret_path' arg, set "
            "'GOOGLE_SHEETS_SECRET_PATH' environment variable, or add to .env file"
        )
        exit()

    # Check the current time
    now = datetime.now(tz=timezone("US/Eastern"))
    date_str = now.strftime("%I:%M on %A, %b %d")
    correct_time = input(f"\n\nIs it curently {date_str}? (y/n) ")
    if correct_time.lower() != "y":
        logger.error("System time is wrong. Please restart")
        exit()

    # Get spreadsheet object
    logger.info(f"Reading google sheet '{config.sheet_name}' using secret at {secret_path}")
    gc = gs.service_account(filename=secret_path)
    _ = gc.open(config.sheet_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config_path",
        type=str,
        default="scripts/initialize_week_sheets.yaml",
        help="Path to the config file",
    )
    args = parser.parse_args()
    config = read_config(args.config_path, ScriptParams)
    main(config)
