import requests
import random
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


# BATCH POLICY API
def get_process_count():
    return requests.get(BASE_URL + "/process-variants/count").json().get("processesCount")


def get_bapol_count():
    return requests.get(BASE_URL + "/batch-policy/count").json().get("batchPolicyCount")


def post_bapol(bapol: dict):
    response = requests.post(BASE_URL + "/batch-policy", json=bapol, headers={"Content-Type": "application/json"})
    assert response.status_code == requests.codes.ok


# INSTANCE ROUTER APU
def new_processes_instance(process_id: int, customer_category: str):
    params = {
        "process-id": process_id,
        "customer-category": customer_category
    }
    response = requests.get(BASE_URL + "/instance-router/start-instance", params=params)
    assert response.status_code == requests.codes.ok
    return response


def get_sum_of_instances(process_id: int):
    params = {
        "process-id": process_id
    }
    response = requests.get(BASE_URL + "/instance-router/aggregate-data", params=params)
    response_json = response.json()
    assert response.status_code == requests.codes.ok
    sum_of_instances = response_json.get('a').get('amount') + response_json.get('b').get('amount')
    return sum_of_instances
