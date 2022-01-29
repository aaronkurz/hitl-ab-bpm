import random
from time import sleep

import requests
from numpy.random import normal

BASE_URL = "http://localhost:5001"
CUSTOMER_CATEGORIES = ["public", "gov"]
AMOUNT_OF_REQUESTS_TO_SEND = 25
NORMAL_DIST_MEAN = 3
NORMAL_DIST_STD_DEV = 1


def get_random_customer_category():
    return CUSTOMER_CATEGORIES[random.randint(0, len(CUSTOMER_CATEGORIES) - 1)]


def get_currently_active_process_id():
    response = requests.get(BASE_URL + "/process-variants/active-meta")
    assert response.status_code == requests.codes.ok
    return response.json().get('id')


def send_request_for_new_processes_instance(process_id):
    params = {
        "process-id": process_id,
        "customer-category": get_random_customer_category()
    }
    response = requests.get(BASE_URL + "/instance-router/start-instance", params=params)
    assert response.status_code == requests.codes.ok
    return response.json().get("camunda_instance_id")


def main():
    currently_active_p_id = get_currently_active_process_id()
    for i in range(AMOUNT_OF_REQUESTS_TO_SEND):
        print(send_request_for_new_processes_instance(currently_active_p_id))
        normal_sample = normal(NORMAL_DIST_MEAN, NORMAL_DIST_STD_DEV)
        sleep_value = normal_sample if normal_sample >= 0 else 0
        sleep(sleep_value)


if __name__ == "__main__":
    main()
