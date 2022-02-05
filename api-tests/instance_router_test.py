from time import sleep

import pytest
import requests

import client_simulator_api_tests as cs
import utils
from config import BASE_URL

CUSTOMER_CATEGORIES = ["public", "gov"]


@pytest.fixture(autouse=True)
def run_before_each_test():
    utils.remove_everything_from_db()
    # ^ before each test
    yield
    # v after each test


@pytest.fixture(scope='module', autouse=True)
def after_all():
    # ^ Will be executed before the first test
    yield
    # v Will be executed after the last test
    utils.remove_everything_from_db()


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
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter_license_fast/helicopter_fast_vA.bpmn",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a', a_hist_min_duration=1,
                             a_hist_max_duration=3)
    utils.post_bapol_currently_active_process(utils.example_batch_policy)
    currently_active_p_id = utils.get_currently_active_process_id()
    cs.start_client_simulation(5)
    sleep(10)
    assert utils.get_sum_of_started_instances_in_batch(currently_active_p_id) == 5
    post_manual_decision(version)
    cs.start_client_simulation(5)
    sleep(10)
    # check that still only 5 got routed inside batch
    assert utils.get_sum_of_started_instances_in_batch(currently_active_p_id) == 5
    # check that 5 additional ones got routes outside batch
    # TODO: add test that makes sure that these are actually of the choice
    assert utils.get_sum_of_started_instances_outside_batch(currently_active_p_id) == 5


def test_instantiation():
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter_license/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter_license/helicopter_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a', a_hist_min_duration=1,
                             a_hist_max_duration=3)
    utils.post_bapol_currently_active_process(utils.example_batch_policy)
    currently_active_p_id = utils.get_currently_active_process_id()
    for i in range(10):
        response = utils.new_processes_instance(currently_active_p_id,
                                                utils.get_random_customer_category(["public", "gov"]))
        assert response.json().get("instantiated") is True
        assert "camundaInstanceId" in response.json().keys()


def test_aggregate_data():
    bapol_5_size = {
        "batchSize": 10,
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
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter_license_fast/helicopter_fast_vA.bpmn",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a', a_hist_min_duration=1,
                             a_hist_max_duration=3)
    assert utils.get_bapol_proposal_count_active_process() == 1
    utils.post_bapol_currently_active_process(bapol_5_size)
    assert utils.get_bapol_count() == 1
    cs.start_client_simulation(10)
    sleep(20)
    assert utils.get_bapol_proposal_count_active_process() == 2
    assert utils.new_open_proposal_exists_active_process() is True
    currently_active_process_id = utils.get_currently_active_process_id()
    params = {
        "process-id": currently_active_process_id
    }
    response = requests.get(BASE_URL + "/instance-router/aggregate-data", params=params)
    response_json = response.json()
    assert response.status_code == requests.codes.ok
    keys = ['numberStarted', 'numberFinished', 'averageDurationSec', 'averageReward']
    # check if the right keys exist for both versions
    for version in ['a', 'b']:
        for key in keys:
            assert key in response_json.get(version).keys()
    assert response_json.get('a').get('numberStarted') + response_json.get('b').get('numberStarted') == 10
    # check if the data has been populated successfully
    for key in keys:
        assert response_json.get('a').get(key) + response_json.get('b').get(key) != 0


def test_aggregate_data_before_instantiation():
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter_license_fast/helicopter_fast_vA.bpmn",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a', a_hist_min_duration=1,
                             a_hist_max_duration=3)
    assert utils.get_bapol_proposal_count_active_process() == 1
    utils.post_bapol_currently_active_process(utils.example_batch_policy)
    assert utils.get_bapol_count() == 1
    currently_active_process_id = utils.get_currently_active_process_id()

    # check if mean duration and reward are None before any instances are started
    params = {
        "process-id": currently_active_process_id
    }
    response = requests.get(BASE_URL + "/instance-router/aggregate-data", params=params)
    response_json = response.json()
    for version in ['a', 'b']:
        assert response_json.get(version).get('averageDurationSec') is None
        assert response_json.get(version).get('averageReward') is None


def test_manual_choice_a():
    """ Test if manual choice of a leads to only instantiating version a afterwards"""
    meta_run_manual_choice('a')


def test_manual_choice_b():
    """ Test if manual choice of b leads to only instantiating version b afterwards"""
    meta_run_manual_choice('b')


def test_two_manual_choices_not_possible():
    """ We want to check that setting a second (manual) decision is not possible """
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter_license_fast/helicopter_fast_vA.bpmn",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a', a_hist_min_duration=1,
                             a_hist_max_duration=3)
    utils.post_bapol_currently_active_process(utils.example_batch_policy)
    post_manual_decision('a')
    try:
        post_manual_decision('b')
        assert False
    except AssertionError:
        pass


def test_client_requests_data_empty():
    """ We want to check if the client requests endpoint works even with zero requested instances """
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter_license_fast/helicopter_fast_vA.bpmn",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a', a_hist_min_duration=1,
                             a_hist_max_duration=3)
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
    assert response.json().get("noTotalRequests") == 5
    assert len(response.json().get("requestsA")) == 5
    assert len(response.json().get("requestsB")) == 5
    assert response.json().get("requestsA")[4] + response.json().get("requestsB")[4] == 5


def test_finished_instances_are_collected():

    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter_license_fast/helicopter_fast_vA.bpmn",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a', a_hist_min_duration=1,
                             a_hist_max_duration=3)
    utils.post_bapol_currently_active_process({
        "batchSize": 10,
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
    })
    params = {
        "process-id": utils.get_currently_active_process_id()
    }
    response = requests.get(BASE_URL + "/instance-router/finished-instance-count", params=params)
    assert response.json().get('finishedInstanceCount') == 0
    cs.start_client_simulation(10)
    sleep(30)
    params = {
        "process-id": utils.get_currently_active_process_id()
    }
    response = requests.get(BASE_URL + "/instance-router/finished-instance-count", params=params)
    assert response.json().get('finishedInstanceCount') > 0


def test_detailed_batch_instance_info():
    bapol_size_5 = {
        "batchSize": 5,
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
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter_license_fast/helicopter_fast_vA.bpmn",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a', a_hist_min_duration=1,
                             a_hist_max_duration=3)
    active_process_id = utils.get_currently_active_process_id()
    # finish three batches
    for i in range(3):
        utils.post_bapol_currently_active_process(bapol_size_5)
        cs.start_client_simulation(5)
        sleep(15)
    # finish half of a batch
    utils.post_bapol_currently_active_process(bapol_size_5)
    cs.start_client_simulation(2)
    sleep(10)
    response = requests.get(BASE_URL + "/batch-policy/count", params={"process-id": active_process_id})
    assert response.json().get('batchPolicyCount') == 4
    # test batch policy instances details
    for i in range(1, 5):
        params = {
            "process-id": active_process_id,
            "batch-number": i
        }
        response = requests.get(BASE_URL + "/instance-router/detailed-data/batch", params=params)
        assert response.status_code == requests.codes.ok
        assert "processId" in response.json().keys()
        assert "batchNumber" in response.json().keys()
        assert "instances" in response.json().keys()
        if i < 4:
            assert len(response.json().get("instances")) == 5
        elif i == 4:
            assert len(response.json().get("instances")) == 2
        for instance in response.json().get("instances"):
            assert "decision" in instance.keys()
            assert "startTime" in instance.keys()
            assert "endTime" in instance.keys()
            assert "reward" in instance.keys()
            assert instance.get("decision") is not None
            assert instance.get("startTime") is not None
            if instance.get("endTime") is None:
                assert instance.get("reward") is None
            if instance.get("reward") is None:
                assert instance.get("endTime") is None
            if instance.get("endTime") is not None:
                assert instance.get("reward") is not None
            if instance.get("reward") is not None:
                assert instance.get("endTime") is not None
