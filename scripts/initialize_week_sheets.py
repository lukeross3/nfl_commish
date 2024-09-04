import argparse
import traceback
from datetime import datetime
from typing import List, Optional

import gspread as gs
import pandas as pd
from gspread_formatting import set_column_widths
from loguru import logger
from pydantic import BaseModel, ConfigDict
from pytz import timezone

from nfl_commish.game import (
    get_the_odds_json,
    get_this_weeks_games,
    parse_the_odds_json,
)
from nfl_commish.settings import Settings
from nfl_commish.utils import read_config


class ScriptParams(BaseModel):
    week: int  # Week number to initialize
    secret_path: Optional[str] = None  # Directory containing google sheets secret
    gspread_username: str = "lukeross"  # Username for google sheets account
    sheet_names: List[str]  # List of google sheet names to update

    model_config = ConfigDict(extra="forbid")


def main(config: ScriptParams):

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

    # Get this week's games
    the_odds_json = get_the_odds_json(api_key=settings.THE_ODDS_API_KEY)
    games = parse_the_odds_json(the_odds_json=the_odds_json)
    this_weeks_games = get_this_weeks_games(games=games)

    # Convert list of games to a pandas DF
    records = [
        {
            "Game ID": game.id,
            "Home Team": game.home_team.value,
            "Away Team": game.away_team.value,
            "Weekday": game.local_date.strftime("%A"),
            "Time (Eastern)": game.local_time.strftime("%I:%M %p"),
            "Date": game.local_date.strftime("%m/%d/%y"),
            "Predicted Winner": None,
            "Confidence Rank": None,
        }
        for game in this_weeks_games
    ]
    df = pd.DataFrame(records)

    # Get user approval to update sheets
    worksheet_name = f"Week {config.week}"
    logger.info(f"Ready to update sheets with new data:\n{df}")
    proceed = input(f"\n\nReady to update sheet '{worksheet_name}' with the above data? (y/n) ")
    if proceed.lower() != "y":
        logger.info("Exiting without updating worksheets")
        exit()

    # Get spreadsheet object
    for sheet_name in config.sheet_names:
        try:
            logger.info(f"Reading google sheet '{sheet_name}' using secret at {secret_path}")
            gc = gs.service_account(filename=secret_path)
            sh = gc.open(sheet_name)

            # Write pandas DF to google sheets
            ws = sh.add_worksheet(title=worksheet_name, cols=len(df.columns), rows=len(df))
            ws.update([df.columns.values.tolist()] + df.values.tolist())
            ws.format("A1:H1", {"textFormat": {"bold": True}})
            set_column_widths(
                ws,
                [
                    ("A", "65"),
                    ("B", "155"),
                    ("C", "155"),
                    ("D", "75"),
                    ("E", "100"),
                    ("F", "60"),
                    ("G", "125"),
                    ("H", "125"),
                ],
            )
            logger.info(f"Successfully updated worksheet '{worksheet_name}' on '{sheet_name}'!")
        except Exception:
            logger.error(
                f"Error updating worksheet '{worksheet_name}' on '{sheet_name}'. "
                f"Traceback:\n\n{traceback.format_exc()}"
            )


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
