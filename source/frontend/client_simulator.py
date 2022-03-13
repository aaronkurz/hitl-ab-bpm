""" Client simulator """
import random
from time import sleep
import requests
from numpy.random import normal
from config import BACKEND_URI
from utils import get_currently_active_process_id

CUSTOMER_CATEGORIES = ["public", "gov"]
NORMAL_DIST_STD_DEV = 0.5


def _get_random_customer_category() -> str:
    """Get random customer category

    :return: "public" or "gov"
    """
    return CUSTOMER_CATEGORIES[random.randint(0, len(CUSTOMER_CATEGORIES) - 1)]


def _send_request_for_new_processes_instance(process_id) -> str:
    """Send a request for a new process instance

    :param process_id: specify process
    :return: Camunda instance id
    """
    params = {
        "process-id": process_id,
        "customer-category": _get_random_customer_category()
    }
    response = requests.get(BACKEND_URI + "/instance-router/start-instance", params=params)
    assert response.status_code == requests.codes.ok  # pylint: disable=no-member
    return response.json().get("camunda_instance_id")


def run_simulation(amount_of_requests: int, avg_interarrival_time: float) -> None:
    """Run simulation

    :param amount_of_requests: How many requests should be sent out
    :param avg_interarrival_time: Average time between instantiation requests
    """
    currently_active_p_id = get_currently_active_process_id()
    for _ in range(amount_of_requests):
        print(_send_request_for_new_processes_instance(currently_active_p_id))
        normal_sample = normal(avg_interarrival_time, NORMAL_DIST_STD_DEV)
        sleep_value = normal_sample if normal_sample >= 0 else 0
        sleep(sleep_value)
