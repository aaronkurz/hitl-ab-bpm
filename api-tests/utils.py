import requests
from config import BASE_URL


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
    assert response.status_code == requests.codes.ok


def remove_all_process_rows():
    assert requests.delete(BASE_URL + "/process-variants").status_code == requests.codes.OK


# BATCH POLICY API
def get_process_count():
    return requests.get(BASE_URL + "/process-variants/count").json().get("processesCount")


def get_bapol_count():
    return requests.get(BASE_URL + "/batch-policy/count").json().get("batchPolicyCount")


def post_bapol(bapol: dict):
    response = requests.post(BASE_URL + "/batch-policy", json=bapol, headers={"Content-Type": "application/json"})
    assert response.status_code == requests.codes.ok
