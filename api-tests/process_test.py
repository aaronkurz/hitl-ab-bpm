from time import sleep
import pytest
import requests
import utils
import client_simulator_api_tests as cs
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
def test_set_process(customer_categories):
    """ Test if setting of new process with variants works """
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter/helicopter_vB.bpmn",
                             customer_categories=customer_categories, default_version='a',
                             path_history="./resources/bpmn/helicopter/helicopter_vA_100.json")
    assert utils.get_process_count() == 1


def test_set_2_processes():
    """ Test if setting of new process with variants works """
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter/helicopter_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a',
                             path_history="./resources/bpmn/helicopter/helicopter_vA_100.json")
    utils.post_processes_a_b("fast",
                             "./resources/bpmn/fast_a_better/fast_a_better_vA.bpmn",
                             "./resources/bpmn/fast_a_better/fast_a_better_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='b',
                             path_history="./resources/bpmn/fast_a_better/fast_a_better_vA_100.json")
    assert utils.get_process_count() == 2


def test_get_active_process_metadata():
    """ Test if receiving of metadata about currently active process works """
    customer_category_groups = ["gov-public", "corporate-sme"]
    for customer_categories in customer_category_groups:
        # given
        utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter/helicopter_vA.bpmn",
                                 "./resources/bpmn/helicopter/helicopter_vB.bpmn",
                                 customer_categories=customer_categories.split('-'),
                                 default_version='a',
                                 path_history="./resources/bpmn/helicopter/helicopter_vA_100.json")
        # when
        response = requests.get(BASE_URL + "/process/active/meta")
        # then
        response_json = response.json()
        assert response.status_code == requests.codes.ok
        assert response_json.get("name") == "helicopter_license"
        assert response_json.get('default_version') == 'a'
        assert response_json.get('id') is not None
        assert response_json.get('customer_categories') == customer_categories  # should be alphabetical
        assert response_json.get('default_interarrival_time_history') == 64.18521
        assert response_json.get('experiment_state') == "Running, before first batch policy has been set"
        assert response_json.get('datetime_added') is not None
        assert response_json.get('datetime_decided') is None
        assert response_json.get('number_batch_policies') == 0
        assert response_json.get('number_instances') == 0
        assert response_json.get("winning_versions") is None
        assert response_json.get("winning_reason") is None


def test_get_active_process_variants_files():
    """ Test of retrieval of active bpmn files works """
    # given
    test_set_2_processes()
    for version in ["a", "b"]:
        # given
        response_given = requests.get(BASE_URL + "/process/active/meta")
        response_given_json = response_given.json()
        assert response_given.status_code == requests.codes.ok
        assert response_given_json.get("name") == "fast"
        # when
        param = {"id": response_given_json.get("id")}
        response = requests.get(BASE_URL + "/process/variant-file/" + version, params=param)
        # then
        assert response.headers['Content-Disposition'].split(";")[0] == "attachment"
        assert response.headers['Content-Disposition'].split(";")[1].split(".")[1] == "bpmn"


def test_files_are_overwritten():
    """
    When a process with the same name is posted, the old one should be replaced
    in the filesystem as well as in the db.
    """
    # given
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter/helicopter_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='b',
                             path_history="./resources/bpmn/helicopter/helicopter_vA_100.json")
    # when
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter/helicopter_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='b',
                             path_history="./resources/bpmn/helicopter/helicopter_vA_100.json")
    # then
    assert utils.get_process_count() == 1


def test_no_process_active_meta_():
    """ When there is no active process/experiment, the active/meta endpoint should return 404 """
    response = requests.get(BASE_URL + "/process/active/meta")
    assert response.status_code == requests.codes.not_found


def test_experiment_state_manual_decision():
    utils.post_processes_a_b("fast", "./resources/bpmn/fast_a_better/fast_a_better_vA.bpmn",
                             "./resources/bpmn/fast_a_better/fast_a_better_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a',
                             path_history="./resources/bpmn/fast_a_better/fast_a_better_vA_100.json")
    utils.post_bapol_currently_active_process(utils.example_batch_policy)
    currently_active_p_id = utils.get_currently_active_process_id()
    cs.start_client_simulation(5, 1)
    assert utils.get_sum_of_started_instances_in_batch(currently_active_p_id) == 5
    utils.post_manual_decision('a')
    exp_state = utils.get_currently_active_process_meta().get('experiment_state')
    assert 'Manual' in exp_state and 'Done' in exp_state


@pytest.mark.parametrize("customer_categories", [["gov", "public"], ["corporate", "sme"]])
def test_experiment_state_cool_off(customer_categories):
    utils.post_processes_a_b("fast", "./resources/bpmn/fast_a_better/fast_a_better_vA.bpmn",
                             "./resources/bpmn/fast_a_better/fast_a_better_vB.bpmn",
                             customer_categories=customer_categories, default_version='a',
                             path_history="./resources/bpmn/fast_a_better/fast_a_better_vA_100.json")
    utils.post_bapol_currently_active_process(utils.example_batch_policy_size(5, customer_categories))
    cs.start_client_simulation(5, 1)
    response_post_cool_off = requests.post(BASE_URL + "/process/active/cool-off")
    assert response_post_cool_off.status_code == requests.codes.ok
    assert 'Cool-Off' in response_post_cool_off.json().get('experimentState')
    exp_state = utils.get_currently_active_process_meta().get('experiment_state')
    assert 'Cool-Off' in exp_state


def test_cool_off_only_after_batch_finished():
    utils.post_processes_a_b("fast", "./resources/bpmn/fast_a_better/fast_a_better_vA.bpmn",
                             "./resources/bpmn/fast_a_better/fast_a_better_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a',
                             path_history="./resources/bpmn/fast_a_better/fast_a_better_vA_100.json")
    # not a batch yet
    response_post_cool_off = requests.post(BASE_URL + "/process/active/cool-off")
    assert response_post_cool_off.status_code == requests.codes.not_found
    # not yet finish a batch
    utils.post_bapol_currently_active_process(utils.example_batch_policy_size(5, ["gov", "public"]))
    cs.start_client_simulation(3, 1)
    response_post_cool_off = requests.post(BASE_URL + "/process/active/cool-off")
    assert response_post_cool_off.status_code == requests.codes.not_found
    cs.start_client_simulation(2, 1)
    # finish batch
    response_post_cool_off = requests.post(BASE_URL + "/process/active/cool-off")
    assert response_post_cool_off.status_code == requests.codes.ok


@pytest.mark.parametrize("customer_categories", [["gov", "public"], ["corporate", "sme"]])
def test_cool_off_period(customer_categories):
    utils.post_processes_a_b("fast", "./resources/bpmn/fast_a_better/fast_a_better_vA.bpmn",
                             "./resources/bpmn/fast_a_better/fast_a_better_vB.bpmn",
                             customer_categories=customer_categories, default_version='a',
                             path_history="./resources/bpmn/fast_a_better/fast_a_better_vA_100.json")
    utils.post_bapol_currently_active_process(utils.example_batch_policy_size(5, customer_categories))
    cs.start_client_simulation(5, 1)
    response_post_cool_off = requests.post(BASE_URL + "/process/active/cool-off")
    assert response_post_cool_off.status_code == requests.codes.ok
    # checking whether cool off is done (should not be the case since the
    # last instance of the first batch is not evaluated
    final_prop_response = requests.get(BASE_URL + "/batch-policy-proposal/final",
                                       params={'process-id': utils.get_currently_active_process_id()})
    assert final_prop_response.status_code == requests.codes.not_found
    decision_json = {
        "decision": [
            {
                "customer_category": customer_categories[0],
                "winning_version": "b"
            },
            {
                "customer_category": customer_categories[1],
                "winning_version": "a"
            }
        ]
    }
    assert requests.post(BASE_URL + "/process/active/winning",
                         json=decision_json).status_code == requests.codes.not_found
    # make sure that meta is in cool-off
    meta = utils.get_currently_active_process_meta()
    assert "In Cool-Off" == meta.get('experiment_state')
    # start some more instances to trigger collection and learning with last open instances
    cs.start_client_simulation(20, 0.5)
    # cool off should be done now, check for final bapol proposal
    meta = utils.get_currently_active_process_meta()
    assert "Cool-Off over, waiting for final decision" == meta.get('experiment_state')
    final_prop_response = requests.get(BASE_URL + "/batch-policy-proposal/final",
                                       params={'process-id': utils.get_currently_active_process_id()})
    assert final_prop_response.status_code == requests.codes.ok
    # winning version should be able to be set
    set_winning_response = requests.post(BASE_URL + "/process/active/winning", json=decision_json)
    assert set_winning_response.status_code == requests.codes.ok
    assert "Done" in set_winning_response.json().get('experiment_state') \
           and "ended normally" in set_winning_response.json().get('experiment_state')
    # check whether winning version and experiment state are correct in metadata
    meta = utils.get_currently_active_process_meta()
    assert "Done" in meta.get('experiment_state') and "ended normally" in meta.get('experiment_state')
    assert meta.get('winning_versions') == [
        {
            "customer_category": customer_categories[0],
            "winning_version": "b"
        },
        {
            "customer_category": customer_categories[1],
            "winning_version": "a"
        }
    ]


def test_cool_off_period_already_all_evaluated():
    """ Test whether entering cool-off after exp inst have already been evaluated works """
    utils.post_processes_a_b("fast", "./resources/bpmn/fast_a_better/fast_a_better_vA.bpmn",
                             "./resources/bpmn/fast_a_better/fast_a_better_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a',
                             path_history="./resources/bpmn/fast_a_better/fast_a_better_vA_100.json")
    utils.post_bapol_currently_active_process(utils.example_batch_policy_size(5, ["gov", "public"]))
    process_id_active = utils.get_currently_active_process_id()
    cs.start_client_simulation(5, 1)
    sleep(20)
    response_manual_trigger = requests.post(BASE_URL + "/process/active/trigger-fetch-learn")
    assert response_manual_trigger.status_code == requests.codes.ok
    response_progress = requests.get(BASE_URL + "/instance-router/aggregate-data/evaluation-progress",
                                       params={"process-id": process_id_active})
    assert response_progress.status_code == requests.codes.ok
    assert response_progress.json().get("alreadyEvaluatedPerc") == 1.0
    response_post_cool_off = requests.post(BASE_URL + "/process/active/cool-off")
    assert response_post_cool_off.status_code == requests.codes.ok
    meta = utils.get_currently_active_process_meta()
    assert "Cool-Off over, waiting for final decision" == meta.get('experiment_state')
    final_prop_response = requests.get(BASE_URL + "/batch-policy-proposal/final",
                                       params={'process-id': utils.get_currently_active_process_id()})
    assert final_prop_response.status_code == requests.codes.ok
    # winning version should be able to be set
    decision_json = {
        "decision": [
            {
                "customer_category": "public",
                "winning_version": "a"
            },
            {
                "customer_category": "gov",
                "winning_version": "b"
            }
        ]
    }
    set_winning_response = requests.post(BASE_URL + "/process/active/winning", json=decision_json)
    assert set_winning_response.status_code == requests.codes.ok
    assert "Done" in set_winning_response.json().get('experiment_state') \
           and "ended normally" in set_winning_response.json().get('experiment_state')
