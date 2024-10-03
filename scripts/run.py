import time

from apscheduler.schedulers.background import BackgroundScheduler

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
    gspread_secret_path=settings.google_sheets_secret_path,
    the_odds_api_key=settings.the_odds_api_key.get_secret_value(),
    copy_timedelta=settings.copy_timedelta,
    scoring_timedelta=settings.scoring_timedelta,
    max_weeks=settings.max_weeks,
)

# Wait for all jobs to complete
while True:
    time.sleep(1)
