import logging

from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.schedulers.background import BackgroundScheduler
from grocery60_be import scheduler as app_scheduler
from grocery60_be import settings

logging.getLogger('apscheduler').setLevel(logging.DEBUG)
scheduler = BackgroundScheduler()
scheduler.add_job(app_scheduler.payout_store, 'interval', minutes=settings.PAYMENT_SCHEDULER_DELAY)
scheduler.add_listener(app_scheduler.notification_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
scheduler.start()