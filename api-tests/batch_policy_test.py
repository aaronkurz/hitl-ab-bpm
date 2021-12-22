import pytest
import requests
import json
from config import BASE_URL


@pytest.fixture(autouse=True)
def run_before_each_test():
    assert requests.delete(BASE_URL + "/batch-policy").status_code == requests.codes.OK
    # ^ before test
    yield
    # v after test


def test_count():
    # when
    response = requests.get(BASE_URL + "/batch-policy/count").json()
    # then
    assert "batchPolicyCount" in response, "Key 'batchPolicyProposal' not found."
    assert response.get("batchPolicyCount") == 0


def test_set_bapol():
    # when
    bapol_json = json.loads("""{
    "batchSize": 200,
    "processDefinitionIdA": "testProcessDefinitionIdA",
    "processDefinitionIdB": "testProcessDefinitionIdB",
    "executionStrategy": [
        {
            "customerCategory": "public",
            "explorationProbabilityA": 1.3,
            "explorationProbabilityB": 0.7
        },
        {
            "customerCategory": "gov",
            "explorationProbabilityA": 0.7,
            "explorationProbabilityB": 0.3
        }
    ]
    }""")
    response = requests.post(BASE_URL + "/batch-policy", json=bapol_json, headers={"Content-Type": "application/json"})
    # then
    assert response.status_code == requests.codes.ok
    assert requests.get(BASE_URL + "/batch-policy/count").json().get("batchPolicyCount") == 1


def test_get_latest():
    # when
    test_set_bapol()
    response = requests.get(BASE_URL + "/batch-policy/latest")
    # then
    assert response.status_code == requests.codes.ok
    response_json = response.json()
    assert response_json.get("batchSize") == 200
    assert response_json.get("processDefinitionIdA") == "testProcessDefinitionIdA"
    assert response_json.get("processDefinitionIdB") == "testProcessDefinitionIdB"
    for i in range(2):
        assert type(response_json.get("executionStrategy")[i].get("customerCategory")) == str
        assert type(response_json.get("executionStrategy")[i].get("explorationProbabilityA")) == float
        assert type(response_json.get("executionStrategy")[i].get("explorationProbabilityB")) == float
