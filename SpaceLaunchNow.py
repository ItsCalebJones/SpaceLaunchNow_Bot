import time

from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.schedulers.background import BackgroundScheduler

import Notifications
from DailyDigest import run_daily, run_weekly
from utils.util import log

TAG = 'Space Launch Now'


if __name__ == '__main__':
    log(TAG, "Initializing server...")
    scheduler = BackgroundScheduler()
    scheduler.start()
    log(TAG, "Created background scheduler.")
    scheduler.add_job(run_daily, trigger='cron', day_of_week='mon-sun', hour=10, minute=30)
    scheduler.add_job(run_weekly, trigger='cron', day_of_week='fri', hour=12, minute=30)
    log(TAG, "Added cronjobs to background scheduler.")
    Notifications.NotificationServer(scheduler).run()
    log(TAG, "Notification Server started.")
    try:
        while True:
            time.sleep(600)
    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
        scheduler.shutdown()
