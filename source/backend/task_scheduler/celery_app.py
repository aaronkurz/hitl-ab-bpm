import config
from celery import Celery
from time import sleep
from datetime import datetime


# Initialize Celery
celery = Celery(
    'worker', 
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND
)

log_file='task_scheduler/celery.log'

@celery.task()
def long_task():
    start_time=datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

    sleep(20)
    end_time=datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

    with open(log_file,'a+') as file:
        file.write(f'Long task taking 20 seconds started at {start_time} and ended at {end_time} \n')

    return 


@celery.task()
def short_task():
    start_time=datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

    sleep(2)
    end_time=datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

    with open(log_file,'a+') as file:
        file.write(f'Short task taking 2 seconds started at {start_time} and ended at {end_time} \n')

    return 

@celery.task()
def custom_task(seconds):
    start_time=datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

    sleep(seconds)
    end_time=datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

    with open(log_file,'a+') as file:
        file.write(f'Custom task taking {seconds} seconds started at {start_time} and ended at {end_time} \n')

    return 

