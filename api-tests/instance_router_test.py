import pytest
import requests
from time import sleep
import client_simulator_api_tests as cs
import utils
from config import BASE_URL
from utils import post_manual_decision


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


def meta_run_manual_choice(version: str, customer_categories: list):
    """ Helps check whether manual decision of version a or b work
    :param version:
    :param customer_categories:
    """
    assert version in ['a', 'b']
    utils.post_processes_a_b("fast", "./resources/bpmn/fast_a_better/fast_a_better_vA.bpmn",
                             "./resources/bpmn/fast_a_better/fast_a_better_vB.bpmn",
                             customer_categories=customer_categories,
                             default_version='a',
                             path_history="./resources/bpmn/fast_a_better/fast_a_better_vA_100.json")
    utils.post_bapol_currently_active_process(utils.example_batch_policy_size(200, customer_categories))
    currently_active_p_id = utils.get_currently_active_process_id()
    cs.start_client_simulation(5, 1)
    assert utils.get_sum_of_started_instances_in_batch(currently_active_p_id) == 5
    post_manual_decision(version)
    cs.start_client_simulation(5, 1)
    # check that still only 5 got routed inside batch
    assert utils.get_sum_of_started_instances_in_batch(currently_active_p_id) == 5
    # check that 5 additional ones got routes outside batch
    # TODO: add test that makes sure that these are actually of the choice
    assert utils.get_sum_of_started_instances_outside_batch(currently_active_p_id) == 5


def test_instantiation():
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter/helicopter_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a',
                             path_history="./resources/bpmn/helicopter/helicopter_vA_100.json")
    utils.post_bapol_currently_active_process(utils.example_batch_policy)
    currently_active_p_id = utils.get_currently_active_process_id()
    for i in range(10):
        response = utils.new_processes_instance(currently_active_p_id,
                                                utils.get_random_customer_category(["public", "gov"]))
        assert response.json().get("instantiated") is True
        assert "camundaInstanceId" in response.json().keys()


def test_instantiation_failing_customer_category():
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter/helicopter_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a',
                             path_history="./resources/bpmn/helicopter/helicopter_vA_100.json")
    utils.post_bapol_currently_active_process(utils.example_batch_policy)
    params = {
        "process-id": utils.get_currently_active_process_id(),
        "customer-category": "enterprise"
    }
    response = requests.get(BASE_URL + "/instance-router/start-instance", params=params)
    assert response.status_code == 400


@pytest.mark.parametrize("customer_categories", [["gov", "public"], ["corporate", "sme"]])
def test_aggregate_data(customer_categories):
    bapol_5_size = {
        "batchSize": 15,
        "executionStrategy": [
            {
                "customerCategory": customer_categories[0],
                "explorationProbabilityA": 0.3,
                "explorationProbabilityB": 0.7
            },
            {
                "customerCategory": customer_categories[1],
                "explorationProbabilityA": 0.7,
                "explorationProbabilityB": 0.3
            }
        ]
    }
    utils.post_processes_a_b("fast", "./resources/bpmn/fast_a_better/fast_a_better_vA.bpmn",
                             "./resources/bpmn/fast_a_better/fast_a_better_vB.bpmn",
                             customer_categories=customer_categories, default_version='a',
                             path_history="./resources/bpmn/fast_a_better/fast_a_better_vA_100.json")
    assert utils.get_bapol_proposal_count_active_process() == 1
    utils.post_bapol_currently_active_process(bapol_5_size)
    assert utils.get_bapol_count() == 1
    cs.start_client_simulation(15, 1)
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
    assert response_json.get('a').get('numberStarted') + response_json.get('b').get('numberStarted') == 15
    # check if the data has been populated successfully
    for key in keys:
        assert response_json.get('a').get(key) + response_json.get('b').get(key) != 0


def test_aggregate_data_before_instantiation():
    utils.post_processes_a_b("fast", "./resources/bpmn/fast_a_better/fast_a_better_vA.bpmn",
                             "./resources/bpmn/fast_a_better/fast_a_better_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a',
                             path_history="./resources/bpmn/fast_a_better/fast_a_better_vA_100.json")
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


@pytest.mark.parametrize("customer_categories", [["gov", "public"], ["corporate", "sme"]])
def test_manual_choice_a(customer_categories):
    """ Test if manual choice of a leads to only instantiating version a afterwards"""
    meta_run_manual_choice('a', customer_categories)


@pytest.mark.parametrize("customer_categories", [["gov", "public"], ["corporate", "sme"]])
def test_manual_choice_b(customer_categories):
    """ Test if manual choice of b leads to only instantiating version b afterwards"""
    meta_run_manual_choice('b', customer_categories)


@pytest.mark.parametrize("customer_categories", [["gov", "public"], ["corporate", "sme"]])
def test_two_manual_choices_not_possible(customer_categories):
    """ We want to check that setting a second (manual) decision is not possible """
    utils.post_processes_a_b("fast", "./resources/bpmn/fast_a_better/fast_a_better_vA.bpmn",
                             "./resources/bpmn/fast_a_better/fast_a_better_vB.bpmn",
                             customer_categories=customer_categories, default_version='a',
                             path_history="./resources/bpmn/fast_a_better/fast_a_better_vA_100.json")
    utils.post_bapol_currently_active_process(utils.example_batch_policy_size(10, customer_categories))
    post_manual_decision('a')
    try:
        post_manual_decision('b')
        assert False
    except AssertionError:
        pass


def test_client_requests_data_empty():
    """ We want to check if the client requests endpoint works even with zero requested instances """
    utils.post_processes_a_b("fast", "./resources/bpmn/fast_a_better/fast_a_better_vA.bpmn",
                             "./resources/bpmn/fast_a_better/fast_a_better_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a',
                             path_history="./resources/bpmn/fast_a_better/fast_a_better_vA_100.json")
    params = {"process-id": utils.get_currently_active_process_id()}
    response = requests.get(BASE_URL + "/instance-router/aggregate-data/client-requests", params=params)
    assert response.status_code == requests.codes.ok
    assert response.json().get("noTotalRequests") == 0
    assert response.json().get("requestsA") == []
    assert response.json().get("requestsB") == []


@pytest.mark.parametrize("customer_categories", [["gov", "public"], ["corporate", "sme"]])
def test_client_requests_data(customer_categories):
    """ Tests whether the client requests data is reasonable """
    meta_run_manual_choice('b', customer_categories)
    params = {"process-id": utils.get_currently_active_process_id()}
    response = requests.get(BASE_URL + "/instance-router/aggregate-data/client-requests", params=params)
    assert response.status_code == requests.codes.ok
    assert response.json().get("noTotalRequests") == 5
    assert len(response.json().get("requestsA")) == 5
    assert len(response.json().get("requestsB")) == 5
    assert response.json().get("requestsA")[4] + response.json().get("requestsB")[4] == 5


def test_finished_instances_are_collected():
    utils.post_processes_a_b("fast", "./resources/bpmn/fast_a_better/fast_a_better_vA.bpmn",
                             "./resources/bpmn/fast_a_better/fast_a_better_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a',
                             path_history="./resources/bpmn/fast_a_better/fast_a_better_vA_100.json")
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
    cs.start_client_simulation(10, 1)
    params = {
        "process-id": utils.get_currently_active_process_id()
    }
    response = requests.get(BASE_URL + "/instance-router/finished-instance-count", params=params)
    assert response.json().get('finishedInstanceCount') > 0


@pytest.mark.parametrize("customer_categories", [["gov", "public"], ["corporate", "sme"]])
def test_detailed_batch_instance_info(customer_categories):
    bapol_size_5 = {
        "batchSize": 5,
        "executionStrategy": [
            {
                "customerCategory": customer_categories[0],
                "explorationProbabilityA": 0.3,
                "explorationProbabilityB": 0.7
            },
            {
                "customerCategory": customer_categories[1],
                "explorationProbabilityA": 0.7,
                "explorationProbabilityB": 0.3
            }
        ]
    }
    utils.post_processes_a_b("fast", "./resources/bpmn/fast_a_better/fast_a_better_vA.bpmn",
                             "./resources/bpmn/fast_a_better/fast_a_better_vB.bpmn",
                             customer_categories=customer_categories, default_version='a',
                             path_history="./resources/bpmn/fast_a_better/fast_a_better_vA_100.json")
    active_process_id = utils.get_currently_active_process_id()
    # finish three batches
    for i in range(3):
        utils.post_bapol_currently_active_process(bapol_size_5)
        cs.start_client_simulation(5, 1)
    # finish half of a batch
    utils.post_bapol_currently_active_process(bapol_size_5)
    cs.start_client_simulation(2, 1)
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
            assert "customerCategory" in instance.keys()
            assert "startTime" in instance.keys()
            assert "endTime" in instance.keys()
            assert "reward" in instance.keys()
            assert "rlProb" in instance.keys()
            assert instance.get("decision") is not None
            assert instance.get("customerCategory") in customer_categories
            assert instance.get("startTime") is not None
            if instance.get("endTime") is None or instance.get("reward") is None or instance.get("rlProb") is None:
                assert instance.get("reward") is None
                assert instance.get("rlProb") is None
                assert instance.get("endTime") is None
            if instance.get("endTime") is not None \
                    or instance.get("reward") is not None \
                    or instance.get("rlProb") is not None:
                assert instance.get("endTime") is not None
                assert instance.get("reward") is not None
                assert instance.get("rlProb") is not None


def test_routing_follows_bapol_b():
    utils.post_processes_a_b("fast", "./resources/bpmn/fast_a_better/fast_a_better_vA.bpmn",
                             "./resources/bpmn/fast_a_better/fast_a_better_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a',
                             path_history="./resources/bpmn/fast_a_better/fast_a_better_vA_100.json")
    utils.post_bapol_currently_active_process({
        "batchSize": 10,
        "executionStrategy": [
            {
                "customerCategory": "public",
                "explorationProbabilityA": 0.0,
                "explorationProbabilityB": 1.0
            },
            {
                "customerCategory": "gov",
                "explorationProbabilityA": 0.0,
                "explorationProbabilityB": 1.0
            }
        ]
    })
    cs.start_client_simulation(10, 1)
    params = {
        "process-id": utils.get_currently_active_process_id(),
        "batch-number": 1
    }
    response = requests.get(BASE_URL + "/instance-router/detailed-data/batch", params=params)
    assert response.status_code == requests.codes.ok
    response_instances = response.json().get("instances")
    assert len(response_instances) == 10
    for instance in response_instances:
        assert instance.get('decision') == 'b'


def test_routing_follows_bapol_a():
    utils.post_processes_a_b("fast", "./resources/bpmn/fast_a_better/fast_a_better_vA.bpmn",
                             "./resources/bpmn/fast_a_better/fast_a_better_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a',
                             path_history="./resources/bpmn/fast_a_better/fast_a_better_vA_100.json")
    utils.post_bapol_currently_active_process({
        "batchSize": 10,
        "executionStrategy": [
            {
                "customerCategory": "public",
                "explorationProbabilityA": 1.0,
                "explorationProbabilityB": 0
            },
            {
                "customerCategory": "gov",
                "explorationProbabilityA": 1.0,
                "explorationProbabilityB": 0
            }
        ]
    })
    cs.start_client_simulation(10, 1)
    params = {
        "process-id": utils.get_currently_active_process_id(),
        "batch-number": 1
    }
    response = requests.get(BASE_URL + "/instance-router/detailed-data/batch", params=params)
    assert response.status_code == requests.codes.ok
    response_instances = response.json().get("instances")
    assert len(response_instances) == 10
    for instance in response_instances:
        assert instance.get('decision') == 'a'


@pytest.mark.parametrize("customer_categories", [["gov", "public"], ["corporate", "sme"]])
def test_routing_follows_bapol_both(customer_categories):
    utils.post_processes_a_b("fast",
                             "resources/bpmn/fast_a_better/fast_a_better_vA.bpmn",
                             "resources/bpmn/fast_a_better/fast_a_better_vB.bpmn",
                             customer_categories=customer_categories, default_version='a',
                             path_history="./resources/bpmn/fast_a_better/fast_a_better_vA_100.json")
    utils.post_bapol_currently_active_process({
        "batchSize": 10,
        "executionStrategy": [
            {
                "customerCategory": customer_categories[0],
                "explorationProbabilityA": 0.5,
                "explorationProbabilityB": 0.5
            },
            {
                "customerCategory": customer_categories[1],
                "explorationProbabilityA": 0.5,
                "explorationProbabilityB": 0.5
            }
        ]
    })
    cs.start_client_simulation(10, 1)
    params = {
        "process-id": utils.get_currently_active_process_id(),
        "batch-number": 1
    }
    response = requests.get(BASE_URL + "/instance-router/detailed-data/batch", params=params)
    assert response.status_code == requests.codes.ok
    response_instances = response.json().get("instances")
    assert len(response_instances) == 10
    a_counter = 0
    b_counter = 0
    for instance in response_instances:
        if instance.get('decision') == 'a':
            a_counter += 1
        elif instance.get('decision') == 'b':
            b_counter += 1
    assert a_counter > 0 and b_counter > 0


def test_a_better_right_decision():
    utils.post_processes_a_b("fast",
                             "resources/bpmn/fast_a_better/fast_a_better_vA.bpmn",
                             "resources/bpmn/fast_a_better/fast_a_better_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a',
                             path_history="./resources/bpmn/fast_a_better/fast_a_better_vA_100.json")
    utils.post_bapol_currently_active_process({
        "batchSize": 100,
        "executionStrategy": [
            {
                "customerCategory": "public",
                "explorationProbabilityA": 0.5,
                "explorationProbabilityB": 0.5
            },
            {
                "customerCategory": "gov",
                "explorationProbabilityA": 0.5,
                "explorationProbabilityB": 0.5
            }
        ]
    })
    cs.start_client_simulation(100, 0.5)
    params = {
        'process-id': utils.get_currently_active_process_id()
    }
    bapol_proposal_response = requests.get(BASE_URL + "/batch-policy-proposal/open", params=params)
    assert bapol_proposal_response.status_code == requests.codes.ok
    proposal_json = bapol_proposal_response.json().get('proposal')
    for execution_strategy in proposal_json.get('executionStrategy'):
        # make sure that version a is preferred (since it is very clearly better)
        assert execution_strategy.get('explorationProbabilityA') > 0.65
        # make sure that the exploration probabilities are 1 in sum
        assert execution_strategy.get('explorationProbabilityA') \
               + execution_strategy.get('explorationProbabilityB') == 1


@pytest.mark.parametrize("customer_categories", [["gov", "public"], ["corporate", "sme"]])
def test_periodic_update_latest_bapol(customer_categories):
    """ Test, if the periodic updating of a batch policy is happening

    Will also focus on test of the endpoint instance-router/aggregate-data/evaluation-progress.
    Update should happen at about every n-th incoming request between batches (n = half of average batch size)
    """
    expected_keyset = ["totalToBeEvaluatedCount",
                       "alreadyEvaluatedCount",
                       "notYetEvaluatedCount",
                       "alreadyEvaluatedPerc",
                       "notYetEvaluatedPerc"]
    utils.post_processes_a_b("helicopter_license",
                             "./resources/bpmn/helicopter/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter/helicopter_vB.bpmn",
                             customer_categories=customer_categories,
                             default_version='a',
                             path_history="./resources/bpmn/helicopter/helicopter_vA_100.json")
    utils.post_bapol_currently_active_process(utils.example_batch_policy_size(10, customer_categories))
    process_id_active = utils.get_currently_active_process_id()

    # -----
    # before any instances have been started, the count values should be zero and the percentage values null
    response_progress_0 = requests.get(BASE_URL + "/instance-router/aggregate-data/evaluation-progress",
                                       params={"process-id": process_id_active})
    assert response_progress_0.status_code == requests.codes.ok
    for key in expected_keyset:
        assert key in response_progress_0.json().keys()
    assert response_progress_0.json().get("totalToBeEvaluatedCount") == 0
    assert response_progress_0.json().get("alreadyEvaluatedCount") == 0
    assert response_progress_0.json().get("notYetEvaluatedCount") == 0
    assert response_progress_0.json().get("alreadyEvaluatedPerc") is None
    assert response_progress_0.json().get("notYetEvaluatedPerc") is None

    # get bapol proposal
    response_bapol_0 = requests.get(BASE_URL + "/batch-policy-proposal/open",
                                    params={'process-id': process_id_active})
    assert response_bapol_0.status_code == requests.codes.ok
    assert response_bapol_0.json().get('newProposalExists') is False

    # test bapol proposal count
    response_bapol_count = requests.get(BASE_URL + "/batch-policy-proposal/count",
                                    params={'process-id': process_id_active})
    assert response_bapol_count.status_code == requests.codes.ok
    assert response_bapol_count.json().get("baPolProposalCount") == 1
    # -----

    cs.start_client_simulation(10, 2)

    # -----
    # since the longer running (avg. 30 s) helicopter processes are used, not all should be finished, but some
    response_progress_1 = requests.get(BASE_URL + "/instance-router/aggregate-data/evaluation-progress",
                                       params={"process-id": process_id_active})
    assert response_progress_1.status_code == requests.codes.ok
    for key in expected_keyset:
        assert key in response_progress_1.json().keys()
    assert response_progress_1.json().get("totalToBeEvaluatedCount") != 0
    assert response_progress_1.json().get("alreadyEvaluatedCount") \
           + response_progress_1.json().get("notYetEvaluatedCount") == \
           response_progress_1.json().get("totalToBeEvaluatedCount")
    assert response_progress_1.json().get("alreadyEvaluatedPerc") is not None
    assert response_progress_1.json().get("notYetEvaluatedPerc") is not None

    # get detailed process data
    params_detailed_batch = {
        "process-id": process_id_active,
        "batch-number": 1
    }
    response_detailed_batch_1 = requests.get(BASE_URL + "/instance-router/detailed-data/batch",
                                             params=params_detailed_batch)
    assert response_detailed_batch_1.status_code == requests.codes.ok
    count_unevaluated_1 = \
        sum(1 for i in response_detailed_batch_1.json().get("instances") if i.get("endTime") is None)
    assert count_unevaluated_1 == response_progress_1.json().get("notYetEvaluatedCount")

    # get bapol proposal
    response_bapol_1 = requests.get(BASE_URL + "/batch-policy-proposal/open",
                            params={'process-id': process_id_active})
    assert response_bapol_1.status_code == requests.codes.ok
    assert response_bapol_1.json().get('newProposalExists') is True

    # make sure that customer categories are correct
    response_cust_cats = []
    for exec_strat in response_bapol_1.json().get('proposal').get('executionStrategy'):
        response_cust_cats.append(exec_strat.get('customerCategory'))
    customer_categories.sort()
    response_cust_cats.sort()
    assert response_cust_cats == customer_categories

    # test bapol proposal count
    response_bapol_count = requests.get(BASE_URL + "/batch-policy-proposal/count",
                                        params={'process-id': process_id_active})
    assert response_bapol_count.status_code == requests.codes.ok
    assert response_bapol_count.json().get("baPolProposalCount") == 2
    # -----

    sleep(10)
    # start more instances outside batch to trigger periodic fetch and learn
    cs.start_client_simulation(25, 2)

    # -----
    # after some more instances (> avg batch size) have been started in between the batch and more time has
    # passed, there should have been more instances that are finished and that have been evaluated
    response_progress_2 = requests.get(BASE_URL + "/instance-router/aggregate-data/evaluation-progress",
                                       params={"process-id": process_id_active})
    assert response_progress_2.status_code == requests.codes.ok
    for key in expected_keyset:
        assert key in response_progress_2.json().keys()
    assert response_progress_2.json().get("totalToBeEvaluatedCount") != 0
    assert response_progress_2.json().get("alreadyEvaluatedCount") \
           + response_progress_2.json().get("notYetEvaluatedCount") == \
           response_progress_2.json().get("totalToBeEvaluatedCount")
    assert response_progress_2.json().get("alreadyEvaluatedPerc") > \
           response_progress_1.json().get("alreadyEvaluatedPerc")
    assert response_progress_2.json().get("notYetEvaluatedPerc") < response_progress_1.json().get("notYetEvaluatedPerc")

    # test whether /instance-router/detailed-data/batch data also changed in accordance with .../evaluation-progress
    response_detailed_batch_2 = requests.get(BASE_URL + "/instance-router/detailed-data/batch",
                                             params=params_detailed_batch)
    assert response_detailed_batch_2.status_code == requests.codes.ok
    count_unevaluated_2 = \
        sum(1 for i in response_detailed_batch_2.json().get("instances") if i.get("endTime") is None)
    assert count_unevaluated_2 == response_progress_2.json().get("notYetEvaluatedCount")

    # get bapol proposal
    response_bapol_2 = requests.get(BASE_URL + "/batch-policy-proposal/open",
                                    params={'process-id': process_id_active})
    assert response_bapol_2.status_code == requests.codes.ok
    assert response_bapol_2.json().get('newProposalExists') is True
    # proposal should have been updated and should (most likely) not be the same
    assert response_bapol_2.json().get('proposal') != response_bapol_1.json().get('proposal')

    # make sure that customer categories are correct
    response_cust_cats = []
    for exec_strat in response_bapol_2.json().get('proposal').get('executionStrategy'):
        response_cust_cats.append(exec_strat.get('customerCategory'))
    customer_categories.sort()
    response_cust_cats.sort()
    assert response_cust_cats == customer_categories

    # test bapol proposal count
    response_bapol_count = requests.get(BASE_URL + "/batch-policy-proposal/count",
                                        params={'process-id': process_id_active})
    assert response_bapol_count.status_code == requests.codes.ok
    assert response_bapol_count.json().get("baPolProposalCount") == 2
    # -----


@pytest.mark.parametrize("customer_categories", [["gov", "public"], ["corporate", "sme"]])
def test_manual_trigger_fetch_learn_outside_batch(customer_categories):
    """ Test, if the endpoint for manually triggering fetch and learn outside of batch works """
    expected_keyset = ["totalToBeEvaluatedCount",
                       "alreadyEvaluatedCount",
                       "notYetEvaluatedCount",
                       "alreadyEvaluatedPerc",
                       "notYetEvaluatedPerc"]
    utils.post_processes_a_b("helicopter_license",
                             "./resources/bpmn/helicopter/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter/helicopter_vB.bpmn",
                             customer_categories=customer_categories,
                             default_version='a',
                             path_history="./resources/bpmn/helicopter/helicopter_vA_100.json")
    utils.post_bapol_currently_active_process(utils.example_batch_policy_size(10, customer_categories))
    process_id_active = utils.get_currently_active_process_id()

    # -----
    # before any instances have been started, the count values should be zero and the percentage values null
    response_progress_0 = requests.get(BASE_URL + "/instance-router/aggregate-data/evaluation-progress",
                                       params={"process-id": process_id_active})
    assert response_progress_0.status_code == requests.codes.ok
    for key in expected_keyset:
        assert key in response_progress_0.json().keys()
    assert response_progress_0.json().get("totalToBeEvaluatedCount") == 0
    assert response_progress_0.json().get("alreadyEvaluatedCount") == 0
    assert response_progress_0.json().get("notYetEvaluatedCount") == 0
    assert response_progress_0.json().get("alreadyEvaluatedPerc") is None
    assert response_progress_0.json().get("notYetEvaluatedPerc") is None

    # get bapol proposal
    response_bapol_0 = requests.get(BASE_URL + "/batch-policy-proposal/open",
                                    params={'process-id': process_id_active})
    assert response_bapol_0.status_code == requests.codes.ok
    assert response_bapol_0.json().get('newProposalExists') is False

    # test bapol proposal count
    response_bapol_count = requests.get(BASE_URL + "/batch-policy-proposal/count",
                                    params={'process-id': process_id_active})
    assert response_bapol_count.status_code == requests.codes.ok
    assert response_bapol_count.json().get("baPolProposalCount") == 1
    # -----

    cs.start_client_simulation(9, 2)
    sleep(10)
    # allow some time for some of them to finish and only finish batch and trigger collection afterwards
    cs.start_client_simulation(1, 2)

    # -----
    # since the longer running (avg. 30 s) helicopter processes are used, not all should be finished, but some
    response_progress_1 = requests.get(BASE_URL + "/instance-router/aggregate-data/evaluation-progress",
                                       params={"process-id": process_id_active})
    assert response_progress_1.status_code == requests.codes.ok
    for key in expected_keyset:
        assert key in response_progress_1.json().keys()
    assert response_progress_1.json().get("totalToBeEvaluatedCount") != 0
    assert response_progress_1.json().get("alreadyEvaluatedCount") \
           + response_progress_1.json().get("notYetEvaluatedCount") == \
           response_progress_1.json().get("totalToBeEvaluatedCount")
    assert response_progress_1.json().get("alreadyEvaluatedPerc") is not None
    assert response_progress_1.json().get("notYetEvaluatedPerc") is not None

    # get detailed process data
    params_detailed_batch = {
        "process-id": process_id_active,
        "batch-number": 1
    }
    response_detailed_batch_1 = requests.get(BASE_URL + "/instance-router/detailed-data/batch",
                                             params=params_detailed_batch)
    assert response_detailed_batch_1.status_code == requests.codes.ok
    count_unevaluated_1 = \
        sum(1 for i in response_detailed_batch_1.json().get("instances") if i.get("endTime") is None)
    assert count_unevaluated_1 == response_progress_1.json().get("notYetEvaluatedCount")

    # get bapol proposal
    response_bapol_1 = requests.get(BASE_URL + "/batch-policy-proposal/open",
                            params={'process-id': process_id_active})
    assert response_bapol_1.status_code == requests.codes.ok
    assert response_bapol_1.json().get('newProposalExists') is True

    # make sure that customer categories are correct
    response_cust_cats = []
    for exec_strat in response_bapol_1.json().get('proposal').get('executionStrategy'):
        response_cust_cats.append(exec_strat.get('customerCategory'))
    customer_categories.sort()
    response_cust_cats.sort()
    assert response_cust_cats == customer_categories

    # test bapol proposal count
    response_bapol_count = requests.get(BASE_URL + "/batch-policy-proposal/count",
                                        params={'process-id': process_id_active})
    assert response_bapol_count.status_code == requests.codes.ok
    assert response_bapol_count.json().get("baPolProposalCount") == 2
    # -----

    sleep(60)
    # trigger periodic fetch and learn
    response_manual_trigger = requests.post(BASE_URL + "/process/active/trigger-fetch-learn")
    assert response_manual_trigger.status_code == requests.codes.ok

    # -----
    # after manual trigger there should have been more instances that are finished and that have been evaluated
    response_progress_2 = requests.get(BASE_URL + "/instance-router/aggregate-data/evaluation-progress",
                                       params={"process-id": process_id_active})
    assert response_progress_2.status_code == requests.codes.ok
    for key in expected_keyset:
        assert key in response_progress_2.json().keys()
    assert response_progress_2.json().get("totalToBeEvaluatedCount") != 0
    assert response_progress_2.json().get("alreadyEvaluatedCount") \
           + response_progress_2.json().get("notYetEvaluatedCount") == \
           response_progress_2.json().get("totalToBeEvaluatedCount")
    assert response_progress_2.json().get("alreadyEvaluatedPerc") > \
           response_progress_1.json().get("alreadyEvaluatedPerc")
    assert response_progress_2.json().get("notYetEvaluatedPerc") < response_progress_1.json().get("notYetEvaluatedPerc")

    # test whether /instance-router/detailed-data/batch data also changed in accordance with .../evaluation-progress
    response_detailed_batch_2 = requests.get(BASE_URL + "/instance-router/detailed-data/batch",
                                             params=params_detailed_batch)
    assert response_detailed_batch_2.status_code == requests.codes.ok
    count_unevaluated_2 = \
        sum(1 for i in response_detailed_batch_2.json().get("instances") if i.get("endTime") is None)
    assert count_unevaluated_2 == response_progress_2.json().get("notYetEvaluatedCount")

    # get bapol proposal
    response_bapol_2 = requests.get(BASE_URL + "/batch-policy-proposal/open",
                                    params={'process-id': process_id_active})
    assert response_bapol_2.status_code == requests.codes.ok
    assert response_bapol_2.json().get('newProposalExists') is True
    # proposal should have been updated and should (most likely) not be the same
    assert response_bapol_2.json().get('proposal') != response_bapol_1.json().get('proposal')

    # make sure that customer categories are correct
    response_cust_cats = []
    for exec_strat in response_bapol_2.json().get('proposal').get('executionStrategy'):
        response_cust_cats.append(exec_strat.get('customerCategory'))
    customer_categories.sort()
    response_cust_cats.sort()
    assert response_cust_cats == customer_categories

    # test bapol proposal count
    response_bapol_count = requests.get(BASE_URL + "/batch-policy-proposal/count",
                                        params={'process-id': process_id_active})
    assert response_bapol_count.status_code == requests.codes.ok
    assert response_bapol_count.json().get("baPolProposalCount") == 2
    # -----


def test_manual_trigger_fetch_learn_before_first_batch_policy():
    """ Before first batch policy, manually triggering fetch and learn should fail """
    utils.post_processes_a_b("helicopter_license",
                             "./resources/bpmn/helicopter/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter/helicopter_vB.bpmn",
                             customer_categories=["public", "gov"],
                             default_version='a',
                             path_history="./resources/bpmn/helicopter/helicopter_vA_100.json")
    response_manual_trigger = requests.post(BASE_URL + "/process/active/trigger-fetch-learn")
    assert response_manual_trigger.status_code == requests.codes.conflict


@pytest.mark.parametrize("customer_categories", [["gov", "public"], ["corporate", "sme"]])
def test_manual_trigger_fetch_learn_in_batch(customer_categories):
    """ When inside batch, manually triggering fetch and learn should fail """
    utils.post_processes_a_b("helicopter_license",
                             "./resources/bpmn/helicopter/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter/helicopter_vB.bpmn",
                             customer_categories=customer_categories,
                             default_version='a',
                             path_history="./resources/bpmn/helicopter/helicopter_vA_100.json")
    utils.post_bapol_currently_active_process(utils.example_batch_policy_size(10, customer_categories))
    response_manual_trigger = requests.post(BASE_URL + "/process/active/trigger-fetch-learn")
    assert response_manual_trigger.status_code == requests.codes.conflict


@pytest.mark.parametrize("customer_categories", [["gov", "public"], ["corporate", "sme"]])
def test_manual_trigger_cool_off_period(customer_categories):
    """ Test whether triggering of manual fetch and learn acts as expected in cool off and afterwards

    In Cool-Off: --> should work
    Cool-Off over, waiting for final decision --> should NOT work
    Done --> should NOT work
    """
    utils.post_processes_a_b("fast", "./resources/bpmn/fast_a_better/fast_a_better_vA.bpmn",
                             "./resources/bpmn/fast_a_better/fast_a_better_vB.bpmn",
                             customer_categories=customer_categories,
                             default_version='a',
                             path_history="./resources/bpmn/fast_a_better/fast_a_better_vA_100.json")
    utils.post_bapol_currently_active_process(utils.example_batch_policy_size(5, customer_categories))
    cs.start_client_simulation(5, 1)
    response_post_cool_off = requests.post(BASE_URL + "/process/active/cool-off")
    assert response_post_cool_off.status_code == requests.codes.ok
    # make sure that meta is in cool-off
    meta = utils.get_currently_active_process_meta()
    assert "In Cool-Off" == meta.get('experiment_state')
    # let instances finish
    sleep(15)
    # trigger periodic fetch and learn
    # should work since last instance of the first batch is not evaluated -> in cool off
    response_manual_trigger = requests.post(BASE_URL + "/process/active/trigger-fetch-learn")
    assert response_manual_trigger.status_code == requests.codes.ok
    # cool off should be done now, check for final bapol proposal
    meta = utils.get_currently_active_process_meta()
    assert meta.get('experiment_state') == "Cool-Off over, waiting for final decision"
    # triggering manual fetch and learn should not work in this experiment state of waiting for final dec
    response_manual_trigger = requests.post(BASE_URL + "/process/active/trigger-fetch-learn")
    assert response_manual_trigger.status_code == requests.codes.conflict
    # winning version should be able to be set
    decision_json = {
        "decision": [
            {
                "customer_category": customer_categories[0],
                "winning_version": "a"
            },
            {
                "customer_category": customer_categories[1],
                "winning_version": "b"
            }
        ]
    }
    set_winning_response = requests.post(BASE_URL + "/process/active/winning", json=decision_json)
    assert set_winning_response.status_code == requests.codes.ok
    assert "Done" in set_winning_response.json().get('experiment_state') \
           and "ended normally" in set_winning_response.json().get('experiment_state')
    # triggering manual fetch and learn should not work in this experiment state of finished
    response_manual_trigger = requests.post(BASE_URL + "/process/active/trigger-fetch-learn")
    assert response_manual_trigger.status_code == requests.codes.conflict
