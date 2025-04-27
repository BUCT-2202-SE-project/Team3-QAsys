
from apscheduler.schedulers.background import BackgroundScheduler

__scheduler = BackgroundScheduler()


def get_scheduler() -> BackgroundScheduler:
    return __scheduler
