from typing import List

import gspread as gs
import pandas as pd
from gspread_formatting import set_column_widths
from loguru import logger

from nfl_commish.game import (
    Game,
    get_completed_games,
    get_the_odds_json,
    get_this_weeks_games,
    is_same_team,
    parse_the_odds_json,
    str_match_team_name,
)
from nfl_commish.settings import Settings
from nfl_commish.utils import ALPHABET, catch_with_logging

settings = Settings()


def get_current_week_num(
    admin_sheet_name: str,
    gspread_secret_path: str,
) -> int:
    """Get the current week number based off the completed games in the admin spreadsheet

    Args:
        admin_sheet_name (str): Name of the admin google sheet
        gspread_secret_path (str): Path to the gspread secret file

    Returns:
        int: The current week number
    """
    # Get the names of the admin sheet's worksheets
    gc = gs.service_account(filename=gspread_secret_path)
    sh = gc.open(admin_sheet_name)
    worksheet_names = [ws.title for ws in sh.worksheets()]

    # Find the max week number
    week_numbers = [int(name.split(" ")[1]) for name in worksheet_names if "Week" in name]
    week_number = max(week_numbers) if week_numbers else 1

    # Determine whether all games are completed
    worksheet_name = f"Week {week_number}"
    ws = sh.worksheet(worksheet_name)
    df = pd.DataFrame(ws.get_all_records())
    winners = df["Winner"].values
    n_completed = sum([1 for winner in winners if winner])

    # If all games are completed, increment the week number
    if n_completed == len(winners):
        week_number += 1
    return week_number


def init_user_week(
    user_sheet_name: str,
    this_weeks_games: List[Game],
    week_number: int,
    gspread_secret_path: str,
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
    week_number: int,
    admin_sheet_name: str,
    player_names: List[str],
    gspread_secret_path: str,
    the_odds_api_key: str,
) -> list[Game]:
    # First get this weeks games
    the_odds_json = get_the_odds_json(api_key=the_odds_api_key, endpoint="events")
    games = parse_the_odds_json(the_odds_json=the_odds_json)
    this_weeks_games = get_this_weeks_games(games=games)
    logger.info(f"Got {len(this_weeks_games)} remaining games for week {week_number}")

    # Update the admin sheet
    try:
        init_admin_week(
            admin_sheet_name=admin_sheet_name,
            this_weeks_games=this_weeks_games,
            week_number=week_number,
            gspread_secret_path=gspread_secret_path,
            player_names=player_names,
        )
        logger.info(f"Updated admin sheet for week {week_number}")
    except Exception as e:
        if f'A sheet with the name "Week {week_number}" already exists.' in str(e):
            logger.info(f"Admin sheet for week {week_number} already exists - skipping")
        else:
            logger.error(f"Failed to initialize admin sheet for week {week_number}:\n\n{str(e)}")

    # Update each of the user sheets
    for player_name in player_names:
        user_sheet_name = f"{player_name} NFL Confidence '24-'25"
        try:
            init_user_week(
                user_sheet_name=user_sheet_name,
                this_weeks_games=this_weeks_games,
                week_number=week_number,
                gspread_secret_path=gspread_secret_path,
            )
            logger.info(f"Updated user sheet {user_sheet_name} for week {week_number}")
        except Exception as e:
            if f'A sheet with the name "Week {week_number}" already exists.' in str(e):
                logger.info(
                    f"User sheet {user_sheet_name} for week {week_number} already exists - skipping"
                )
            else:
                logger.error(
                    f"Failed to initialize user sheet {user_sheet_name} "
                    f"for week {week_number}:\n\n{str(e)}"
                )

    # Return the list of games for downstream use
    return this_weeks_games


def copy_predictions_to_admin(
    week_number: int,
    admin_sheet_name: str,
    player_names: List[str],
    gspread_secret_path: str,
    game_ids: List[str] = None,
) -> None:
    """Copy the predictions from the user sheets to the admin sheet for a given week, keeping
    existing formatting intact

    Args:
        week_number (int): The week number to update
        admin_sheet_name (str): The name of the admin google sheet
        player_names (List[str]): List of player names
        gspread_secret_path (str): Path to the gspread secret file
        game_ids (List[str], optional): List of game IDs to update. If None, all games are updated.
            Defaults to None.
    """
    # Get the admin sheet
    gc = gs.service_account(filename=gspread_secret_path)
    sh = gc.open(admin_sheet_name)
    worksheet_name = f"Week {week_number}"
    ws = sh.worksheet(worksheet_name)
    df = pd.DataFrame(ws.get_all_records())

    # Get the user sheets
    logger.info(f"Copying week {week_number} picks to admin sheet for games: {game_ids}")
    for player_name in player_names:
        user_sheet_name = f"{player_name} NFL Confidence '24-'25"
        user_sheet = gc.open(user_sheet_name)
        user_ws = user_sheet.worksheet(worksheet_name)
        user_df = pd.DataFrame(user_ws.get_all_records())

        # Find the predicted winner and confidence for each game
        for _, row in user_df.iterrows():
            game_id = row["Game ID"]

            # Skip if we are only updating a subset of games
            if game_ids is not None and game_id not in game_ids:
                continue
            pred = row["Predicted Winner"]
            conf = row["Confidence Rank"]
            home_team = row["Home Team"]
            away_team = row["Away Team"]

            # Classify the user's pick into one of the 2 standardized team names
            if not pred or not conf:
                logger.warning(f"Player {player_name} missing prediction for game {game_id}")
                pred = settings.missed_pred_str
                conf = 0
            else:
                pred = catch_with_logging(
                    fn=str_match_team_name,
                    args={"str_to_classify": pred, "candidate_labels": [home_team, away_team]},
                )

            # Find the row and columns to update in the admin sheet
            admin_row_idx = df[df["Game ID"] == game_id].index[0]
            pred_col_idx = df.columns.get_loc(f"{player_name} Predicted")
            conf_col_idx = df.columns.get_loc(f"{player_name} Confidence")

            # Check for existing values
            existing_pred = df.iloc[admin_row_idx][f"{player_name} Predicted"]
            existing_conf = df.iloc[admin_row_idx][f"{player_name} Confidence"]
            if existing_pred or existing_conf:
                logger.info(
                    f"Player {player_name} already has a prediction for game {game_id} - skipping"
                )
                continue

            # Update the admin sheet
            ws.update_cell(admin_row_idx + 2, pred_col_idx + 1, pred)
            ws.update_cell(admin_row_idx + 2, conf_col_idx + 1, conf)


def update_admin_total_scores_from_week_scores(
    week_number: int,
    admin_sheet_name: str,
    player_names: List[str],
    gspread_secret_path: str,
) -> None:
    """Copy the current point total from the week sheet to the scores/total sheet, within the
    admin sheet.

    TODO: TEST THIS FUNCTION
    """
    # Get the week sheet as a DF
    gc = gs.service_account(filename=gspread_secret_path)
    sh = gc.open(admin_sheet_name)
    worksheet_name = f"Week {week_number}"
    week_ws = sh.worksheet(worksheet_name)
    week_df = pd.DataFrame(week_ws.get_all_records())

    # Get the scores sheet as a DF
    scores_ws = sh.worksheet("Scores")
    scores_df = pd.DataFrame(scores_ws.get_all_records())

    # For each player, get the sum of their scores for the week
    for player_name in player_names:
        week_score = pd.to_numeric(
            week_df[f"{player_name} Points"], errors="coerce", downcast="integer"
        ).sum()
        row_idx = week_number + 1
        col_idx = scores_df.columns.get_loc(player_name) + 1
        scores_ws.update_cell(row_idx, col_idx, week_score)


def update_admin_with_completed_games(
    week_number: int,
    admin_sheet_name: str,
    player_names: List[str],
    gspread_secret_path: str,
    the_odds_api_key: str,
) -> None:
    # Get the admin sheet
    gc = gs.service_account(filename=gspread_secret_path)
    sh = gc.open(admin_sheet_name)
    worksheet_name = f"Week {week_number}"
    ws = sh.worksheet(worksheet_name)
    df = pd.DataFrame(ws.get_all_records())

    # Find the game IDs from this week that do not yet have a winner
    to_update = []
    for _, row in df.iterrows():
        if not row["Winner"]:
            to_update.append(row["Game ID"])

    # Get a list of completed games
    the_odds_json = get_the_odds_json(api_key=the_odds_api_key, endpoint="scores")
    games = parse_the_odds_json(the_odds_json=the_odds_json)
    completed_games = get_completed_games(games=games)

    # Keep only those with an ID we want to update
    completed_games = list(filter(lambda x: x.id in to_update, completed_games))
    logger.info(f"Updating {len(completed_games)} games for week {week_number}")

    # For each game, update the winner and each of the players results
    for game in completed_games:
        row_idx = df[df["Game ID"] == game.id].index[0]
        winner_col_idx = df.columns.get_loc("Winner")
        ws.update_cell(row_idx + 2, winner_col_idx + 1, game.winner.value)

        # Update each player's points
        for player_name in player_names:

            # Classify the user's pick into one of the 2 standardized team names
            pred = df.iloc[row_idx][f"{player_name} Predicted"]
            conf = df.iloc[row_idx][f"{player_name} Confidence"]
            if not pred or not conf:
                logger.warning(f"Player {player_name} missing prediction for game {game.id}")
                pred = settings.missed_pred_str
            else:
                pred = catch_with_logging(
                    fn=str_match_team_name,
                    args={
                        "str_to_classify": pred,
                        "candidate_labels": [game.home_team.value, game.away_team.value],
                    },
                )

            # Get the point value
            points = 0
            if pred is not None and is_same_team(pred, game.winner.value):
                points = conf

            # Update the points in the admin sheet
            points_col_idx = df.columns.get_loc(f"{player_name} Points")
            ws.update_cell(row_idx + 2, points_col_idx + 1, points)
            logger.info(f"Updated {player_name} for game {game.id} with {points} points")

    # Copy the current point totals over from the week sheet to the score/totals sheet
    update_admin_total_scores_from_week_scores(
        week_number=week_number,
        admin_sheet_name=admin_sheet_name,
        player_names=player_names,
        gspread_secret_path=gspread_secret_path,
    )
