import pytest
import requests
import utils
from config import BASE_URL


@pytest.fixture(autouse=True)
def run_before_each_test():
    assert requests.delete(BASE_URL + "/batch-policy-proposal").status_code == requests.codes.OK
    assert requests.delete(BASE_URL + "/batch-policy").status_code == requests.codes.OK
    utils.remove_all_process_rows()
    # ^ before each test
    yield
    # v after each test


@pytest.fixture(scope='module', autouse=True)
def after_all():
    # ^ Will be executed before the first test
    yield
    # v Will be executed after the last test
    assert requests.delete(BASE_URL + "/batch-policy-proposal").status_code == requests.codes.OK
    assert requests.delete(BASE_URL + "/batch-policy").status_code == requests.codes.OK
    utils.remove_all_process_rows()


def test_count():
    """ Test if count of batch policies is zero when relevant db tables empty """
    # given (just fixture)
    # when
    response = requests.get(BASE_URL + "/batch-policy/count").json()
    # then
    assert "batchPolicyCount" in response, "Key 'batchPolicyCount' not found."
    assert utils.get_bapol_count() == 0


def test_set_bapol():
    """ Test if setting of new batch policy works and whether it has an associated batch policy proposal """
    # given
    utils.post_processes_a_b("helicopter_license",
                             "./resources/bpmn/helicopter_license/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter_license/helicopter_vB.bpmn",
                             customer_categories=["public", "gov"],
                             default_version='a')
    utils.post_processes_a_b("helicopter_license_fast",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vA.bpmn",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vB.bpmn",
                             customer_categories=["public", "gov"],
                             default_version='a')
    utils.post_bapol(utils.example_batch_policy)
    assert utils.get_bapol_count() == 1


def test_get_latest():
    """ Test if retrieval of the latest batch policy works """
    # given
    test_set_bapol()
    # when
    response = requests.get(BASE_URL + "/batch-policy/latest")
    # then
    assert response.status_code == requests.codes.ok
    response_json = response.json()
    assert response_json.get("batchSize") == 200
    assert response_json.get("prevBaPolPropId") is not None
    assert type(response_json.get("processId")) == int
    for i in range(2):
        assert type(response_json.get("executionStrategy")[i].get("customerCategory")) == str
        assert type(response_json.get("executionStrategy")[i].get("explorationProbabilityA")) == float
        assert type(response_json.get("executionStrategy")[i].get("explorationProbabilityB")) == float
