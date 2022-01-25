# Put stuff here, that is useful for more than one API test module
# (if it is only relevant for one, please consider putting it in that module)
import random

import requests

from config import BASE_URL


# GENERAL
def get_random_customer_category(list_of_customer_categories: [str]):
    return list_of_customer_categories[random.randint(0, len(list_of_customer_categories) - 1)]


# PROCESS VARIANTS API
def post_processes_a_b(process_name: str, path_a: str, path_b: str):
    # given
    files_in = {
        "variantA": open(path_a),
        "variantB": open(path_b)
    }
    # when
    response = requests.post(BASE_URL + "/process-variants/" + process_name, files=files_in)
    # then
    assert response.status_code == requests.codes.ok, "Setting of process failed: " + str(response.content)


def remove_all_process_rows():
    response = requests.delete(BASE_URL + "/process-variants")
    assert response.status_code == requests.codes.OK, "Deletion of process rows failed: " + str(response.content)


def get_currently_active_process_id():
    response = requests.get(BASE_URL + "/process-variants/active-meta")
    assert response.status_code == requests.codes.ok
    return response.json().get('id')


# LEARNING POLICY API
example_learning_policy = {
    "experimentationLength": 200,
    "experimentationDecay": 5,
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
    return requests.get(BASE_URL + "/process-variants/count").json().get("processesCount")


def get_lepol_count():
    return requests.get(BASE_URL + "/learning-policy/count").json().get("learningPolicyCount")


def post_lepol(lepol: dict):
    response = requests.post(BASE_URL + "/learning-policy", json=lepol, headers={"Content-Type": "application/json"})
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
