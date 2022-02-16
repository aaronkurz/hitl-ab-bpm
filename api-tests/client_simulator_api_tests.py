""" Use this to simulate client requests in the API tests"""
import random
from time import sleep

import requests
from numpy.random import normal

from config import BASE_URL
from utils import get_currently_active_process_id

CUSTOMER_CATEGORIES = ["public", "gov"]
NORMAL_DIST_STD_DEV = 0.1


def _get_random_customer_category():
    return CUSTOMER_CATEGORIES[random.randint(0, len(CUSTOMER_CATEGORIES) - 1)]


def send_request_for_new_processes_instance(process_id):
    params = {
        "process-id": process_id,
        "customer-category": _get_random_customer_category()
    }
    response = requests.get(BASE_URL + "/instance-router/start-instance", params=params)
    assert response.status_code == requests.codes.ok
    return response.json().get("camunda_instance_id")


def start_client_simulation(amount_of_requests_to_send: int, avg_break_sec: float):
    currently_active_p_id = get_currently_active_process_id()
    for i in range(amount_of_requests_to_send):
        send_request_for_new_processes_instance(currently_active_p_id)
        normal_sample = normal(avg_break_sec, NORMAL_DIST_STD_DEV)
        sleep_value = normal_sample if normal_sample >= 0 else 0
        sleep(sleep_value)
