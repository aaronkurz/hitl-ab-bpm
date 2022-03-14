""" Helpful utilities for frontend """
import requests

from config import BACKEND_URI


def currently_active_process_exists() -> bool:
    """Check whether there is an active process/experiment in backend

    :raises RuntimeError: Unexpected response from backend
    :return: True or false
    """
    response = requests.get(BACKEND_URI + "process/active/meta")
    if response.status_code == 404:
        return False
    if response.status_code == requests.codes.ok:  # pylint: disable=no-member
        return True
    raise RuntimeError("Unexpected response from backend.")


def get_currently_active_process_id() -> int:
    """Get currently active process id

    :return: Id of currently active process/experiment
    """
    response = requests.get(BACKEND_URI + "process/active/meta")
    assert response.status_code == requests.codes.ok  # pylint: disable=no-member
    return response.json().get("id")


def get_currently_active_process_meta() -> any:
    """ Get metadata of currently active process

    :return: JSON of metadata
    """
    response = requests.get(BACKEND_URI + "process/active/meta")
    assert response.status_code == requests.codes.ok  # pylint: disable=no-member
    return response.json()


def post_manual_decision(manual_decision: str) -> bool:
    """Post manual decision

    :param manual_decision: 'a' or 'b'
    :return: True or false
    """
    assert manual_decision in ['a', 'b']
    params = {
        "process-id": get_currently_active_process_id(),
        "version-decision": manual_decision
    }
    response = requests.post(BACKEND_URI + "process/active/manual-decision", params=params)
    return response.status_code == requests.codes.ok  # pylint: disable=no-member


def get_bapol_count() -> int:
    """ Get amount of batch policies for currently active process

    :return: Amount of batch policies for currently active process
    """
    return requests.get(BACKEND_URI + "batch-policy/count",
                        params={"process-id": get_currently_active_process_id()}).json().get("batchPolicyCount")
