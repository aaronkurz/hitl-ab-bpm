import pytest
import requests
import client_simulator_api_tests as cs
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


@pytest.mark.parametrize("customer_categories", [["gov", "public"], ["corporate", "sme"]])
def test_first_one_automatically_created(customer_categories):
    """ Test whether the first, naive bapol proposal is created for a new proposal """
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter/helicopter_vB.bpmn",
                             customer_categories=customer_categories,
                             default_version='a',
                             path_history="./resources/bpmn/helicopter/helicopter_vA_100.json")
    assert utils.get_process_count() == 1
    params = {
        'process-id': utils.get_currently_active_process_id()
    }
    response = requests.get(BASE_URL + "/batch-policy-proposal/open", params=params)
    assert response.status_code == requests.codes.ok
    assert True is response.json().get('newProposalExists')

    # make sure that customer categories are correct
    response_cust_cats = []
    for exec_strat in response.json().get('proposal').get('executionStrategy'):
        response_cust_cats.append(exec_strat.get('customerCategory'))
    customer_categories.sort()
    response_cust_cats.sort()
    assert response_cust_cats == customer_categories

    # make sure the id is of the process just posted
    bapol_prop_process_id = response.json().get('proposal').get('processId')
    response_process_meta = requests.get(BASE_URL + "/process/active/meta")
    current_process_id = response_process_meta.json().get('id')
    assert current_process_id == bapol_prop_process_id
    
    # make sure there is no batch policy for proposal yet
    assert None is response.json().get('proposal').get('baPolId')


@pytest.mark.parametrize("customer_categories", [["gov", "public"], ["corporate", "sme"]])
def test_new_proposal_after_batch(customer_categories):
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter/helicopter_vB.bpmn",
                             customer_categories=customer_categories, default_version='a',
                             path_history="./resources/bpmn/helicopter/helicopter_vA_100.json")
    assert utils.get_bapol_proposal_count_active_process() == 1
    utils.post_bapol_currently_active_process(utils.example_batch_policy_size(5, customer_categories))
    assert utils.get_bapol_count() == 1
    cs.start_client_simulation(5, 1)
    assert utils.get_bapol_proposal_count_active_process() == 2
    response = requests.get(BASE_URL + "/batch-policy-proposal/open",
                            params={'process-id': utils.get_currently_active_process_id()})
    assert response.status_code == requests.codes.ok
    assert True is response.json().get('newProposalExists')

    # make sure that customer categories are correct
    response_cust_cats = []
    for exec_strat in response.json().get('proposal').get('executionStrategy'):
        response_cust_cats.append(exec_strat.get('customerCategory'))
    customer_categories.sort()
    response_cust_cats.sort()
    assert response_cust_cats == customer_categories


def test_requests_in_between_batches():
    bapol_5_size = {
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
    utils.post_processes_a_b("fast", "./resources/bpmn/fast_a_better/fast_a_better_vA.bpmn",
                             "./resources/bpmn/fast_a_better/fast_a_better_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a',
                             path_history="./resources/bpmn/fast_a_better/fast_a_better_vA_100.json")
    # one open proposal at the beginning
    assert utils.get_bapol_proposal_count_active_process() == 1
    # setting a batch policy with size 5 and finishing it
    utils.post_bapol_currently_active_process(bapol_5_size)
    assert utils.get_bapol_count() == 1
    cs.start_client_simulation(5, 1)
    # making sure after first batch is finished that there are two proposals
    assert utils.get_bapol_proposal_count_active_process() == 2
    assert utils.new_open_proposal_exists_active_process() is True
    # starting 5 instances in between batches
    cs.start_client_simulation(5, 1)
    # setting a new bapol
    utils.post_bapol_currently_active_process(bapol_5_size)
    assert utils.get_bapol_count() == 2
    # not finishing bapol
    cs.start_client_simulation(3, 1)
    # making sure that there is no new proposal yet
    assert utils.new_open_proposal_exists_active_process() is False
    assert utils.get_bapol_proposal_count_active_process() == 2
    # finishing bapol
    cs.start_client_simulation(2, 1)
    # making sure there is a new proposal
    assert utils.new_open_proposal_exists_active_process() is True
    assert utils.get_bapol_proposal_count_active_process() == 3


def test_after_manual_decision_no_proposal():
    bapol_5_size = utils.example_batch_policy_size(5, ["gov", "public"])
    utils.post_processes_a_b("fast", "./resources/bpmn/fast_a_better/fast_a_better_vA.bpmn",
                             "./resources/bpmn/fast_a_better/fast_a_better_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a',
                             path_history="./resources/bpmn/fast_a_better/fast_a_better_vA_100.json")
    # one open proposal at the beginning
    assert utils.new_open_proposal_exists_active_process()
    # setting a batch policy with size 5 and finishing it
    utils.post_bapol_currently_active_process(bapol_5_size)
    cs.start_client_simulation(5, 1)
    # making sure after first batch is finished that there is a new open proposal
    assert utils.new_open_proposal_exists_active_process()
    utils.post_manual_decision('b')
    # assert that after manual decision there is no open proposal anymore
    assert not utils.new_open_proposal_exists_active_process()


def test_bapol_prop_goes_away_cool_off():
    """ The open batch policy proposal should not be served anymore after the cool-off period has been started """
    utils.post_processes_a_b("fast", "./resources/bpmn/fast_a_better/fast_a_better_vA.bpmn",
                             "./resources/bpmn/fast_a_better/fast_a_better_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a',
                             path_history="./resources/bpmn/fast_a_better/fast_a_better_vA_100.json")
    # finish a batch
    utils.post_bapol_currently_active_process(utils.example_batch_policy_size(5, ["gov", "public"]))
    cs.start_client_simulation(5, 1)
    # one open proposal
    assert utils.new_open_proposal_exists_active_process()
    # start cool-off period
    response_post_cool_off = requests.post(BASE_URL + "/process/active/cool-off")
    assert response_post_cool_off.status_code == requests.codes.ok
    # no more open proposal
    assert not utils.new_open_proposal_exists_active_process()
