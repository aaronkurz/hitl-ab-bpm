from time import sleep

import pytest
import requests

import client_simulator_api_tests as cs
import utils
from config import BASE_URL

CUSTOMER_CATEGORIES = ["public", "gov"]


def post_manual_decision(manual_decision: str):
    """ Set a manual decision for currently active process in backend """
    assert manual_decision in ['a', 'b']
    params = {
        "process-id": utils.get_currently_active_process_id(),
        "version-decision": manual_decision
    }
    response = requests.post(BASE_URL + "/instance-router/manual-decision", params=params)
    assert response.status_code == requests.codes.ok


def meta_run_manual_choice(version: str):
    """ Helps check whether manual decision of version a or b work """
    assert version in ['a', 'b']
    utils.post_processes_a_b("helicopter_license",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vA.bpmn",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vB.bpmn")
    utils.post_lepol(utils.example_learning_policy)
    currently_active_p_id = utils.get_currently_active_process_id()
    cs.start_client_simulation(5)
    sleep(10)
    assert utils.get_sum_of_instances(currently_active_p_id) == 5
    instances_a_before = utils.get_amount_of_instances(currently_active_p_id, 'a')
    instances_b_before = utils.get_amount_of_instances(currently_active_p_id, 'b')
    post_manual_decision(version)
    cs.start_client_simulation(5)
    sleep(10)
    assert utils.get_sum_of_instances(currently_active_p_id) == 10
    instances_a_after = utils.get_amount_of_instances(currently_active_p_id, 'a')
    instances_b_after = utils.get_amount_of_instances(currently_active_p_id, 'b')

    if version == 'a':
        assert instances_a_before + 5 == instances_a_after
        assert instances_b_before == instances_b_after
    if version == 'b':
        assert instances_a_before == instances_a_after
        assert instances_b_before + 5 == instances_b_after


@pytest.fixture(autouse=True)
def run_before_each_test():
    utils.remove_all_process_rows()
    # ^ before each test
    yield
    # v after each test


@pytest.fixture(scope='module', autouse=True)
def after_all():
    # ^ Will be executed before the first test
    yield
    # v Will be executed after the last test
    utils.remove_all_process_rows()


def test_instantiation():
    utils.post_processes_a_b("helicopter_license",
                             "./resources/bpmn/helicopter_license/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter_license/helicopter_vB.bpmn")
    utils.post_lepol(utils.example_learning_policy)
    currently_active_p_id = utils.get_currently_active_process_id()
    for i in range(10):
        response = utils.new_processes_instance(currently_active_p_id,
                                                utils.get_random_customer_category(["public", "gov"]))
        assert response.json().get("instantiated") is True
        assert "camundaInstanceId" in response.json().keys()


def test_aggregate_data():
    utils.post_processes_a_b("helicopter_license",
                             "./resources/bpmn/helicopter_license/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter_license/helicopter_vB.bpmn")
    utils.post_lepol(utils.example_learning_policy)
    currently_active_p_id = utils.get_currently_active_process_id()
    for i in range(10):
        response = utils.new_processes_instance(currently_active_p_id,
                                                utils.get_random_customer_category(["public", "gov"]))
        assert response.json().get("instantiated") is True
        assert "camundaInstanceId" in response.json().keys()
    assert utils.get_sum_of_instances(currently_active_p_id) == 10


def test_manual_choice_a():
    """ Test if manual choice of a leads to only instantiating version a afterwards"""
    meta_run_manual_choice('a')


def test_manual_choice_b():
    """ Test if manual choice of b leads to only instantiating version b afterwards"""
    meta_run_manual_choice('b')


def test_two_manual_choices_not_possible():
    """ We want to check that setting a second (manual) decision is not possible """
    utils.post_processes_a_b("helicopter_license",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vA.bpmn",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vB.bpmn")
    utils.post_lepol(utils.example_learning_policy)
    post_manual_decision('a')
    try:
        post_manual_decision('b')
        assert False
    except AssertionError:
        pass


def test_client_requests_data_empty():
    """ We want to check if the client requests endpoint works even with zero requested instances """
    utils.post_processes_a_b("helicopter_license",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vA.bpmn",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vB.bpmn")
    params = {"process-id": utils.get_currently_active_process_id()}
    response = requests.get(BASE_URL + "/instance-router/aggregate-data/client-requests", params=params)
    assert response.status_code == requests.codes.ok
    assert response.json().get("noTotalRequests") == 0
    assert response.json().get("requestsA") == []
    assert response.json().get("requestsB") == []


def test_client_requests_data():
    """ Tests whether the client requests data is reasonable """
    meta_run_manual_choice('b')
    params = {"process-id": utils.get_currently_active_process_id()}
    response = requests.get(BASE_URL + "/instance-router/aggregate-data/client-requests", params=params)
    assert response.status_code == requests.codes.ok
    assert response.json().get("noTotalRequests") == 10
    assert len(response.json().get("requestsA")) == 10
    assert len(response.json().get("requestsB")) == 10
    assert response.json().get("requestsA")[9] + response.json().get("requestsB")[9] == 10
