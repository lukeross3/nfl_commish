from datetime import datetime, timedelta
from typing import List

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from loguru import logger

from nfl_commish.admin import (
    copy_predictions_to_admin,
    get_current_week_num,
    init_week,
    update_admin_with_completed_games,
)


def schedule_commish_tasks(
    scheduler: BackgroundScheduler,
    admin_sheet_name: str,
    player_names: List[str],
    gspread_secret_path: str,
    the_odds_api_key: str,
    copy_timedelta: timedelta = timedelta(minutes=5),
    scoring_timedelta: timedelta = timedelta(hours=5),
    max_weeks: int = 18,
):
    # First determine the current week number
    week_number = get_current_week_num(
        admin_sheet_name=admin_sheet_name,
        gspread_secret_path=gspread_secret_path,
    )
    if week_number > max_weeks:
        logger.warning(f"Max week {max_weeks} reached, no more tasks will be scheduled")
        return
    logger.info(f"Scheduling tasks for week {week_number}")

    # Initialize the current week
    this_weeks_games = init_week(
        week_number=week_number,
        admin_sheet_name=admin_sheet_name,
        player_names=player_names,
        gspread_secret_path=gspread_secret_path,
        the_odds_api_key=the_odds_api_key,
    )

    # Get a map from game start times to game IDs
    start_to_id_map = {}
    for game in this_weeks_games:
        if game.local_commence_time not in start_to_id_map:
            start_to_id_map[game.local_commence_time] = []
        start_to_id_map[game.local_commence_time].append(game.id)

    # Schedule the tasks to copy predictions to the admin sheet for each unique start time
    for start_time, game_ids in start_to_id_map.items():
        date_trigger = DateTrigger(start_time - copy_timedelta)
        scheduler.add_job(
            copy_predictions_to_admin,
            date_trigger,
            [
                week_number,
                admin_sheet_name,
                player_names,
                gspread_secret_path,
                game_ids,
            ],
        )
        logger.info(
            f"Scheduled task to lock in picks {copy_timedelta} before {start_time} "
            f"kickoff - games: {game_ids}"
        )

    # Get a set of unique start times, rounding to the nearest hour to reduce frequency
    rounded_start_times = set()
    for game in this_weeks_games:
        rounded_start_times.add(game.local_commence_time.replace(minute=0, second=0, microsecond=0))

    # Schedule the tasks to update the admin sheet with completed games for each rounded start time
    logger.info(f"Scheduling tasks to update scores {scoring_timedelta} after kickoff")
    for start_time in rounded_start_times:
        date_trigger = DateTrigger(start_time + scoring_timedelta)
        scheduler.add_job(
            update_admin_with_completed_games,
            date_trigger,
            [
                week_number,
                admin_sheet_name,
                player_names,
                gspread_secret_path,
                the_odds_api_key,
            ],
        )
        logger.info(
            f"Scheduled task to update scores {scoring_timedelta} after (rounded) "
            f"{start_time} kickoff"
        )

    # Schedule this same task for next week on tuesday at 2 am
    today = datetime.now()
    next_week = today
    if today.weekday() == 1:  # Edge case if today is Tuesday - want a week from today
        next_week += timedelta(days=1)
    while next_week.weekday() != 1:  # Monday is 0, Tuesday is 1
        next_week += timedelta(days=1)
    next_week = next_week.replace(hour=2, minute=0, second=0, microsecond=0)
    date_trigger = DateTrigger(next_week)
    scheduler.add_job(
        schedule_commish_tasks,
        date_trigger,
        [
            scheduler,
            admin_sheet_name,
            player_names,
            gspread_secret_path,
            the_odds_api_key,
            copy_timedelta,
            scoring_timedelta,
        ],
    )
    logger.info(f"Scheduled next week's scheduler to run at {next_week}")
