import datetime
import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from loguru import logger

# Create a scheduler
scheduler = BackgroundScheduler()
scheduler.start()


# Define the function that is to be executed
def my_job(text):
    logger.info(text)


# Define a datetime for the job to run
run_date = datetime.datetime.now() + datetime.timedelta(seconds=1)
date_trigger_1 = DateTrigger(run_date)
run_date_2 = datetime.datetime.now() + datetime.timedelta(seconds=2)
date_trigger_2 = DateTrigger(run_date_2)

# Store the job in a variable in case we want to cancel it
job = scheduler.add_job(my_job, date_trigger_1, ["first job done!"])
job2 = scheduler.add_job(my_job, date_trigger_2, ["second job done!"])

while len(scheduler.get_jobs()) > 0:
    pass
time.sleep(0.1)
logger.info("All jobs complete")
