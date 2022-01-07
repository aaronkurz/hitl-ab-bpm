import pytest
import utils

CUSTOMER_CATEGORIES = ["public", "gov"]


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
    utils.post_bapol({
        "batchSize": 200,
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
    })
    currently_active_p_id = utils.get_currently_active_process_id()
    for i in range(10):
        response = utils.new_processes_instance(currently_active_p_id, utils.get_random_customer_category(["public", "gov"]))
        assert response.json().get("instantiated") is True
        assert "camundaInstanceId" in response.json().keys()


def test_aggregate_data():
    utils.post_processes_a_b("helicopter_license",
                             "./resources/bpmn/helicopter_license/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter_license/helicopter_vB.bpmn")
    utils.post_bapol({
        "batchSize": 200,
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
    })
    currently_active_p_id = utils.get_currently_active_process_id()
    for i in range(10):
        response = utils.new_processes_instance(currently_active_p_id,
                                                utils.get_random_customer_category(["public", "gov"]))
        assert response.json().get("instantiated") is True
        assert "camundaInstanceId" in response.json().keys()
    assert utils.get_sum_of_instances(currently_active_p_id) == 10
