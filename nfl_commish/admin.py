from datetime import datetime
from typing import List

import gspread as gs
import pandas as pd
from gspread_formatting import set_column_widths
from loguru import logger
from pydantic import BaseModel, ConfigDict
from pytz import timezone

from nfl_commish.game import Game, get_the_odds_json, parse_the_odds_json
from nfl_commish.utils import ALPHABET, str_to_col_width


def get_current_week_num() -> int:
    """Get the current week number based off the completed games in the admin spreadsheet

    ##### TODO #####
    """
    # Get the names of the admin sheet's worksheets

    # Find the max week number

    # Determine whether all games are completed
    return 1


def init_user_week(
    user_sheet_name: str, this_weeks_games: List[Game], week_number: int, gspread_secret_path: str
) -> None:
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

    # Get spreadsheet object
    gc = gs.service_account(filename=gspread_secret_path)
    sh = gc.open(user_sheet_name)

    # Write pandas DF to google sheets
    worksheet_name = f"Week {week_number}"
    ws = sh.add_worksheet(title=worksheet_name, cols=len(df.columns), rows=len(df))
    ws.update([df.columns.values.tolist()] + df.values.tolist())

    # Update formatting
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


def init_admin_week(
    admin_sheet_name: str,
    this_weeks_games: List[Game],
    week_number: int,
    gspread_secret_path: str,
    player_names: List[str],
) -> None:
    """Initialize a new week on the admin google sheet by adding a new worksheet with the
    week's games
    """
    # Convert list of games to a pandas DF
    records = [
        {
            "Game ID": game.id,
            "Home Team": game.home_team.value,
            "Away Team": game.away_team.value,
            "Weekday": game.local_date.strftime("%A"),
            "Time (Eastern)": game.local_time.strftime("%I:%M %p"),
            "Date": game.local_date.strftime("%m/%d/%y"),
        }
        for game in this_weeks_games
    ]
    df = pd.DataFrame(records)

    # Add some empty columns
    df["Winner"] = ""
    for player_name in sorted(player_names):
        df[f"{player_name} Predicted"] = ""
        df[f"{player_name} Confidence"] = ""
        df[f"{player_name} Points"] = ""

    # Get spreadsheet object
    gc = gs.service_account(filename=gspread_secret_path)
    sh = gc.open(admin_sheet_name)

    # Write pandas DF to google sheets
    worksheet_name = f"Week {week_number}"
    ws = sh.add_worksheet(title=worksheet_name, cols=len(df.columns), rows=len(df))
    ws.update([df.columns.values.tolist()] + df.values.tolist())

    # Format Header
    ws.format("1:1", {"textFormat": {"bold": True}, "borders": {"bottom": {"style": "SOLID"}}})

    # Format column widths
    team_name_width = "155"
    col_widths = [
        ("A", "65"),
        ("B", team_name_width),
        ("C", team_name_width),
        ("D", "75"),
        ("E", "100"),
        ("F", "60"),
        ("G", team_name_width),
    ]
    for i, col_name in enumerate(df.columns):
        if ALPHABET[i] in [col[0] for col in col_widths]:
            continue
        if "Predicted" in col_name:
            col_widths.append((ALPHABET[i], team_name_width))
        else:
            val = 22 + (7 * len(col_name))
            col_widths.append((ALPHABET[i], str(val)))
    set_column_widths(ws, col_widths)

    # Format column borders
    to_border = ["G"]
    start_idx = ALPHABET.index("G") + 3
    while start_idx < len(df.columns) and len(to_border) < len(player_names):
        to_border.append(ALPHABET[start_idx])
        start_idx += 3
    for col in to_border:
        ws.format(f"{col}2:{col}", {"borders": {"right": {"style": "SOLID"}}})
        ws.format(  # Special case for header to keep the bottom border
            f"{col}1", {"borders": {"bottom": {"style": "SOLID"}, "right": {"style": "SOLID"}}}
        )


def init_week(
    user_sheet_names: List[str],
    admin_sheet_name: str,
    gspread_secret_path: str,
    the_odds_api_key: str,
) -> list[datetime]:
    # Determine the current week number
    week_number = get_current_week_num()
    logger.info(f"Initializing week {week_number}")

    # First get this weeks games
    this_weeks_games = parse_the_odds_json(
        get_the_odds_json(api_key=the_odds_api_key, endpoint="events")
    )
    logger.info(f"Got {len(this_weeks_games)} remaining games for week {week_number}")

    # Update the admin sheet
    init_admin_week(
        admin_sheet_name=admin_sheet_name,
        this_weeks_games=this_weeks_games,
        week_number=week_number,
    )
    logger.info(f"Updated admin sheet for week {week_number}")

    # Update each of the user sheets
    for user_sheet_name in user_sheet_names:
        try:
            init_user_week(
                user_sheet_name=user_sheet_name,
                this_weeks_games=this_weeks_games,
                week_number=week_number,
                gspread_secret_path=gspread_secret_path,
            )
            logger.info(f"Updated user sheet {user_sheet_name} for week {week_number}")
        except Exception as e:
            logger.error(
                f"Failed to initialize user sheet {user_sheet_name} for week {week_number}:\n\n{str(e)}"
            )

    # Return the list of unique game commence times
    return list(set(game.commence_time for game in this_weeks_games))
