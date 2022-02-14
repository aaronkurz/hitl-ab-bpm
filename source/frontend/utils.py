""" Helpful utilities for frontend """
import requests

from config import BACKEND_URI


def currently_active_process_exists():
    response = requests.get(BACKEND_URI + "process/active/meta")
    if response.status_code == 404:
        return False
    if response.status_code == requests.codes.ok:
        return True
    else:
        raise RuntimeError("Unexpected response from backend.")


def get_currently_active_process_id():
    response = requests.get(BACKEND_URI + "process/active/meta")
    assert response.status_code == requests.codes.ok
    return response.json().get("id")


def get_currently_active_process_meta():
    response = requests.get(BACKEND_URI + "process/active/meta")
    assert response.status_code == requests.codes.ok
    return response.json()


def post_manual_decision(manual_decision: str) -> bool:
    assert manual_decision in ['a', 'b']
    params = {
        "process-id": get_currently_active_process_id(),
        "version-decision": manual_decision
    }
    response = requests.post(BACKEND_URI + "process/active/manual-decision")
    return response.status_code == requests.codes.ok


def get_bapol_count():
    return requests.get(BACKEND_URI + "batch-policy/count",
                        params={"process-id": get_currently_active_process_id()}).json().get("batchPolicyCount")
