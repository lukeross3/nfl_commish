import time

from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

from nfl_commish.scheduling import schedule_commish_tasks
from nfl_commish.settings import Settings

# Global settings/values
player_names = [
    "Luke",
    "Andrew",
    "Shivam",
    "Spuff",
    "Benjie",
    "Brett",
]
admin_sheet_name = "NFL Confidence '24-'25"
settings = Settings()

# Create a scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Schedule the commish tasks
schedule_commish_tasks(
    scheduler=scheduler,
    admin_sheet_name=admin_sheet_name,
    player_names=player_names,
    gspread_secret_path=settings.gspread_secret_path,
    the_odds_api_key=settings.the_odds_api_key,
    copy_timedelta=settings.copy_timedelta,
    scoring_timedelta=settings.scoring_timedelta,
    max_weeks=settings.max_weeks,
)

# Wait for all jobs to complete
while len(scheduler.get_jobs()) > 0:
    time.sleep(1)

# If we made it here, the season is over!
logger.warning("No more scheduled tasks, the season is over!")
