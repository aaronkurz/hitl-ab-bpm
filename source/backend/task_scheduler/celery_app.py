""" Celery tool """
from time import sleep
from datetime import datetime
from task_scheduler import config
from celery import Celery


# Initialize Celery
celery = Celery(
    'worker',
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND
)

LOG_FILE= 'task_scheduler/celery.log'

@celery.task()
def long_task():
    """ Long Task """
    start_time=datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

    sleep(20)
    end_time=datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

    with open(LOG_FILE, 'a+', encoding='utf-8') as file:
        file.write(f'Long task taking 20 seconds started at {start_time} and ended at {end_time} \n')


@celery.task()
def short_task():
    """ Short Task """
    start_time=datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

    sleep(2)
    end_time=datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

    with open(LOG_FILE, 'a+', encoding='utf-8') as file:
        file.write(f'Short task taking 2 seconds started at {start_time} and ended at {end_time} \n')


@celery.task()
def custom_task(seconds):
    """ Custom Task """
    start_time=datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

    sleep(seconds)
    end_time=datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

    with open(LOG_FILE, 'a+', encoding='utf-8') as file:
        file.write(f'Custom task taking {seconds} seconds started at {start_time} and ended at {end_time} \n')
