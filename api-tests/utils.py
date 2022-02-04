# Put stuff here, that is useful for more than one API test module
# (if it is only relevant for one, please consider putting it in that module)
import requests
import random

import requests

from config import BASE_URL


# GENERAL
def get_random_customer_category(list_of_customer_categories: [str]):
    return list_of_customer_categories[random.randint(0, len(list_of_customer_categories) - 1)]

def remove_everything_from_db():
    # TODO add endpoint for all tables
    #  https://stackoverflow.com/questions/11233128/how-to-clean-the-database-dropping-all-records-using-sqlalchemy
    delete_all_proposals()
    remove_all_process_rows()


# PROCESS API
def post_processes_a_b(process_name: str, path_a: str, path_b: str, customer_categories: [str], default_version: str,
                       a_hist_min_duration: float, a_hist_max_duration: float):
    # given
    files_in = {
        "variantA": open(path_a),
        "variantB": open(path_b)
    }
    params = {
        'customer-categories': "-".join(customer_categories),
        'default-version': default_version,
        "a-hist-min-duration": a_hist_min_duration,
        "a-hist-max-duration": a_hist_max_duration
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


def post_bapol_currently_active_process(bapol: dict):
    params = {
        'process-id': get_currently_active_process_id()
    }
    response = requests.post(BASE_URL + "/batch-policy", json=bapol, headers={"Content-Type": "application/json"},
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


# BATCH POLICY PROPOSAL
def delete_all_proposals():
    response = requests.delete(BASE_URL + "/batch-policy-proposal")
    assert response.status_code == requests.codes.ok, "Deletion of bapol proposal rows failed: " + str(response.content)


def get_bapol_proposal_count_active_process():
    params = {
        'process-id': get_currently_active_process_id()
    }
    response = requests.get(BASE_URL + "/batch-policy-proposal/count", params=params)
    assert response.status_code == requests.codes.ok
    return response.json().get('baPolProposalCount')


def new_open_proposal_exists_active_process():
    response = requests.get(BASE_URL + "/batch-policy-proposal/open",
                            params={'process-id': get_currently_active_process_id()})
    assert response.status_code == requests.codes.ok
    return response.json().get('newProposalExists')
