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


def test_set_process():
    """ Test if setting of new process with variants works """
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter_license/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter_license/helicopter_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a',
                             path_history="./resources/bpmn/helicopter_license/2000a.json")
    assert utils.get_process_count() == 1


def test_set_2_processes():
    """ Test if setting of new process with variants works """
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter_license/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter_license/helicopter_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a',
                             path_history="./resources/bpmn/helicopter_license/2000a.json")
    utils.post_processes_a_b("helicopter_license_fast",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vA.bpmn",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='b',
                             path_history="./resources/bpmn/helicopter_license_fast/2000a.json")
    assert utils.get_process_count() == 2


def test_get_active_process_metadata():
    """ Test if receiving of metadata about currently active process works """
    # given
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter_license/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter_license/helicopter_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a',
                             path_history="./resources/bpmn/helicopter_license/2000a.json")
    # when
    response = requests.get(BASE_URL + "/process/active/meta")
    # then
    response_json = response.json()
    assert response.status_code == requests.codes.ok
    assert response_json.get("name") == "helicopter_license"
    assert response_json.get('defaultVersion') == 'a'
    assert response_json.get('id') is not None
    assert response_json.get('customerCategories') == "public-gov"
    assert response_json.get('defaultInterarrivalTimeHistory') == 0.98
    assert response_json.get('experimentState') == "Running"
    assert response_json.get('addedTime') is not None
    assert response_json.get('decisionTime') is None
    assert response_json.get("winningVersion") is None


def test_get_active_process_variants_files():
    """ Test of retrieval of active bpmn files works """
    # given
    test_set_2_processes()
    for version in ["a", "b"]:
        # given
        response_given = requests.get(BASE_URL + "/process/active/meta")
        response_given_json = response_given.json()
        assert response_given.status_code == requests.codes.ok
        assert response_given_json.get("name") == "helicopter_license_fast"
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
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter_license/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter_license/helicopter_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='b',
                             path_history="./resources/bpmn/helicopter_license/2000a.json")
    # when
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter_license/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter_license/helicopter_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='b',
                             path_history="./resources/bpmn/helicopter_license/2000a.json")
    # then
    assert utils.get_process_count() == 1


def test_no_process_active_meta_():
    """ When there is no active process/experiment, the active/meta endpoint should return 404 """
    response = requests.get(BASE_URL + "/process/active/meta")
    assert response.status_code == requests.codes.not_found


def test_experiment_state_manual_decision():
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter_license_fast/helicopter_fast_vA.bpmn",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a',
                             path_history="./resources/bpmn/helicopter_license_fast/2000a.json")
    utils.post_bapol_currently_active_process(utils.example_batch_policy)
    currently_active_p_id = utils.get_currently_active_process_id()
    cs.start_client_simulation(5, 1)
    assert utils.get_sum_of_started_instances_in_batch(currently_active_p_id) == 5
    utils.post_manual_decision('a')
    exp_state = utils.get_currently_active_process_meta().get('experimentState')
    assert 'Manual' in exp_state and 'Done' in exp_state


def test_experiment_state_cool_off():
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter_license_fast/helicopter_fast_vA.bpmn",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a',
                             path_history="./resources/bpmn/helicopter_license_fast/2000a.json")
    utils.post_bapol_currently_active_process(utils.example_batch_policy_size(5))
    cs.start_client_simulation(5, 1)
    response_post_cool_off = requests.post(BASE_URL + "/process/active/cool-off")
    assert response_post_cool_off.status_code == requests.codes.ok
    assert 'Cool-Off' in response_post_cool_off.json().get('experimentState')
    exp_state = utils.get_currently_active_process_meta().get('experimentState')
    assert 'Cool-Off' in exp_state


def test_cool_off_only_after_batch_finished():
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter_license_fast/helicopter_fast_vA.bpmn",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a',
                             path_history="./resources/bpmn/helicopter_license_fast/2000a.json")
    # not a batch yet
    response_post_cool_off = requests.post(BASE_URL + "/process/active/cool-off")
    assert response_post_cool_off.status_code == requests.codes.not_found
    # not yet finish a batch
    utils.post_bapol_currently_active_process(utils.example_batch_policy_size(5))
    cs.start_client_simulation(3, 1)
    response_post_cool_off = requests.post(BASE_URL + "/process/active/cool-off")
    assert response_post_cool_off.status_code == requests.codes.not_found
    cs.start_client_simulation(2, 1)
    # finish batch
    response_post_cool_off = requests.post(BASE_URL + "/process/active/cool-off")
    assert response_post_cool_off.status_code == requests.codes.ok


def test_cool_off_period():
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter_license_fast/helicopter_fast_vA.bpmn",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a',
                             path_history="./resources/bpmn/helicopter_license_fast/2000a.json")
    utils.post_bapol_currently_active_process(utils.example_batch_policy_size(5))
    cs.start_client_simulation(5, 1)
    response_post_cool_off = requests.post(BASE_URL + "/process/active/cool-off")
    assert response_post_cool_off.status_code == requests.codes.ok
    # checking whether cool off is done (should not be the case since the
    # last instance of the first batch is not evaluated
    final_prop_response = requests.get(BASE_URL + "/batch-policy-proposal/final",
                                       params={'process-id': utils.get_currently_active_process_id()})
    assert final_prop_response.status_code == requests.codes.not_found
    assert requests.post(BASE_URL + "/process/active/winning",
                         params={'winning-version': 'b'}).status_code == requests.codes.not_found
    # make sure that meta is in cool-off
    meta = utils.get_currently_active_process_meta()
    assert "In Cool-Off" == meta.get('experimentState')
    # start some more instances to trigger collection and learning with last open instances
    cs.start_client_simulation(20, 0.5)
    # cool off should be done now, check for final bapol proposal
    meta = utils.get_currently_active_process_meta()
    assert "Cool-Off over, waiting for final decision" == meta.get('experimentState')
    final_prop_response = requests.get(BASE_URL + "/batch-policy-proposal/final",
                                       params={'process-id': utils.get_currently_active_process_id()})
    assert final_prop_response.status_code == requests.codes.ok
    # winning version should be able to be set
    set_winning_response = requests.post(BASE_URL + "/process/active/winning", params={'winning-version': 'b'})
    assert set_winning_response.status_code == requests.codes.ok
    assert "Done" in set_winning_response.json().get('experimentState') \
           and "ended normally" in set_winning_response.json().get('experimentState')
    # check whether winning version and experiment state are correct in metadata
    meta = utils.get_currently_active_process_meta()
    assert "Done" in meta.get('experimentState') and "ended normally" in meta.get('experimentState')
    assert meta.get('winningVersion') == 'b'
