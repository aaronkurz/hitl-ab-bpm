""" Helpful utilities for frontend """
import requests

from config import BACKEND_URI


def get_currently_active_process_id():
    response = requests.get(BACKEND_URI + "/process/active-meta")
    assert response.status_code == requests.codes.ok
    return response.json().get("id")


def post_manual_decision(manual_decision: str) -> bool:
    assert manual_decision in ['a', 'b']
    params = {
        "process-id": get_currently_active_process_id(),
        "version-decision": manual_decision
    }
    response = requests.post(BACKEND_URI + "/instance-router/manual-decision", params=params)
    return response.status_code == requests.codes.ok
