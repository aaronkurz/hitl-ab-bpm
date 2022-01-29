# Put stuff here, that is useful for more than one API test module
# (if it is only relevant for one, please consider putting it in that module)
import requests
import random

import requests

from config import BASE_URL


# GENERAL
def get_random_customer_category(list_of_customer_categories: [str]):
    return list_of_customer_categories[random.randint(0, len(list_of_customer_categories) - 1)]


# PROCESS API
def post_processes_a_b(process_name: str, path_a: str, path_b: str, customer_categories: [str], default_version: str):
    # given
    files_in = {
        "variantA": open(path_a),
        "variantB": open(path_b)
    }
    params = {
        'customer-categories': "-".join(customer_categories),
        'default-version': default_version
    }
    # when
    response = requests.post(BASE_URL + "/process/" + process_name, files=files_in, params=params)
    # then
    assert response.status_code == requests.codes.ok, "Setting of process failed: " + str(response.content)


def remove_all_process_rows():
    response = requests.delete(BASE_URL + "/process")
    assert response.status_code == requests.codes.ok, "Deletion of process rows failed: " + str(response.content)


def get_currently_active_process_id():
    response = requests.get(BASE_URL + "/process/active-meta")
    assert response.status_code == requests.codes.ok
    return response.json().get('id')


# BATCH POLICY API
example_batch_policy = {
        "batchSize": 200,
        "executionStrategy": [
            {
                "customerCategory": "public",
                "explorationProbabilityA": 0.3,
                "explorationProbabilityB": 0.7
            },
            {
                "customerCategory": "gov",
                "explorationProbabilityA": 0.7,
                "explorationProbabilityB": 0.3
            }
        ]
    }


def get_process_count():
    return requests.get(BASE_URL + "/process/count").json().get("processesCount")


def get_bapol_count():
    return requests.get(BASE_URL + "/batch-policy/count").json().get("batchPolicyCount")


def post_bapol(lepol: dict):
    params = {
        'process-id': get_currently_active_process_id()
    }
    response = requests.post(BASE_URL + "/batch-policy", json=lepol, headers={"Content-Type": "application/json"},
                             params=params)
    assert response.status_code == requests.codes.ok


# INSTANCE ROUTER API
def new_processes_instance(process_id: int, customer_category: str):
    params = {
        "process-id": process_id,
        "customer-category": customer_category
    }
    response = requests.get(BASE_URL + "/instance-router/start-instance", params=params)
    assert response.status_code == requests.codes.ok
    return response


def get_sum_of_instances(process_id: int):
    return get_amount_of_instances(process_id, 'a') + get_amount_of_instances(process_id, 'b')


def get_amount_of_instances(process_id: int, version: str):
    assert version in ['a', 'b']
    params = {
        "process-id": process_id
    }
    response = requests.get(BASE_URL + "/instance-router/aggregate-data", params=params)
    response_json = response.json()
    assert response.status_code == requests.codes.ok
    return response_json.get(version).get('amount')
