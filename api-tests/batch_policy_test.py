import pytest
import requests

import utils
from config import BASE_URL


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


def test_count():
    """ Test if count of batch policies is zero when relevant db tables empty """
    # given
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter_license/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter_license/helicopter_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a', a_hist_min_duration=1,
                             a_hist_max_duration=3)
    # when
    response = requests.get(BASE_URL + "/batch-policy/count",
                            params={"process-id": utils.get_currently_active_process_id()}).json()
    # then
    assert "batchPolicyCount" in response, "Key 'batchPolicyCount' not found."
    assert "processId" in response
    assert utils.get_bapol_count() == 0


def test_set_bapol():
    """ Test if setting of new batch policy works and whether it has an associated batch policy proposal """
    # given
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter_license/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter_license/helicopter_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a', a_hist_min_duration=1,
                             a_hist_max_duration=3)
    utils.post_processes_a_b("helicopter_license_fast",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vA.bpmn",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a', a_hist_min_duration=1,
                             a_hist_max_duration=3)
    utils.post_bapol_currently_active_process(utils.example_batch_policy)
    assert utils.get_bapol_count() == 1


def test_set_bapol_failing_json():
    # given
    utils.post_processes_a_b("helicopter_license_fast",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vA.bpmn",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a', a_hist_min_duration=1,
                             a_hist_max_duration=3)
    bapol = {
        "batchSize": 200,
        "executionStrategy": [
            {
                "customerCategory": "public",
                "explorationProbability_A": 0.3,
                "explorationProbabilityB": 0.7
            },
            {
                "customer_Category": "gov",
                "explorationProbabilityA": 0.7,
                "explorationProbabilityB": 0.3
            }
        ]
    }
    params = {
        'process-id': utils.get_currently_active_process_id()
    }
    response = requests.post(BASE_URL + "/batch-policy", json=bapol, headers={"Content-Type": "application/json"},
                             params=params)
    assert response.status_code == 400


def test_set_bapol_failing_customer_category():
    # given
    utils.post_processes_a_b("helicopter_license_fast",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vA.bpmn",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a', a_hist_min_duration=1,
                             a_hist_max_duration=3)
    bapol = {
        "batchSize": 200,
        "executionStrategy": [
            {
                "customerCategory": "public",
                "explorationProbability_A": 0.3,
                "explorationProbabilityB": 0.7
            },
            {
                "customer_Category": "enterprise",
                "explorationProbabilityA": 0.7,
                "explorationProbabilityB": 0.3
            }
        ]
    }
    params = {
        'process-id': utils.get_currently_active_process_id()
    }
    response = requests.post(BASE_URL + "/batch-policy", json=bapol, headers={"Content-Type": "application/json"},
                             params=params)
    assert response.status_code == 400


def test_get_latest():
    """ Test if retrieval of the latest batch policy works """
    # given
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter_license/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter_license/helicopter_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a', a_hist_min_duration=1,
                             a_hist_max_duration=3)
    utils.post_bapol_currently_active_process({
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
    })
    # when
    response = requests.get(BASE_URL + "/batch-policy/latest")
    # then
    assert response.status_code == requests.codes.ok
    response_json = response.json()
    assert response_json.get("batchSize") == 200
    assert response_json.get("prevBaPolPropId") is not None
    assert response_json.get("processId") == utils.get_currently_active_process_id()
    for i in range(2):
        exec_strat = response_json.get("executionStrategy")[i]
        if exec_strat.get("customerCategory") == "public":
            assert exec_strat.get("explorationProbabilityA") == 0.3
            assert exec_strat.get("explorationProbabilityB") == 0.7
        if exec_strat.get("customerCategory") == "gov":
            assert exec_strat.get("explorationProbabilityA") == 0.7
            assert exec_strat.get("explorationProbabilityB") == 0.3
