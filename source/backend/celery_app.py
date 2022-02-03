import config
from celery import Celery


# Initialize Celery
celery = Celery(
    'worker', 
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND
)


@celery.task()
def func1():
    
    return 5 