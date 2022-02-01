import pytest
import requests
import utils
from config import BASE_URL


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


def test_set_process():
    """ Test if setting of new process with variants works """
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter_license/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter_license/helicopter_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a', a_hist_min_duration=1,
                             a_hist_max_duration=3)
    assert utils.get_process_count() == 1


def test_set_2_processes():
    """ Test if setting of new process with variants works """
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter_license/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter_license/helicopter_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a', a_hist_min_duration=1,
                             a_hist_max_duration=3)
    utils.post_processes_a_b("helicopter_license_fast",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vA.bpmn",
                             "./resources/bpmn/helicopter_license_fast/helicopter_fast_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='b', a_hist_min_duration=1,
                             a_hist_max_duration=3)
    assert utils.get_process_count() == 2


def test_get_active_process_metadata():
    """ Test if receiving of metadata about currently active process works """
    # given
    test_set_2_processes()
    # when
    response = requests.get(BASE_URL + "/process/active-meta")
    # then
    response_json = response.json()
    assert response.status_code == requests.codes.ok
    assert response_json.get("name") == "helicopter_license_fast"
    assert response_json.get('defaultVersion') == 'b'
    assert response_json.get('id') is not None
    assert response_json.get('addedTime') is not None
    assert response_json.get('decisionTime') is None
    assert response_json.get("winningVersion") is None


def test_get_active_process_variants_files():
    """ Test of retrieval of active bpmn files works """
    # given
    test_set_2_processes()
    for version in ["a", "b"]:
        # given
        response_given = requests.get(BASE_URL + "/process/active-meta")
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
                             customer_categories=["public", "gov"], default_version='b', a_hist_min_duration=1,
                             a_hist_max_duration=3)
    # when
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter_license/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter_license/helicopter_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='b', a_hist_min_duration=1,
                             a_hist_max_duration=3)
    # then
    assert utils.get_process_count() == 1


def test_cascading_delete():
    """ Test if the cascading delete works

    If I delete a process, the corresponding batch policies and instance db entries should be deleted too
    """
    # given
    utils.post_processes_a_b("helicopter_license", "./resources/bpmn/helicopter_license/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter_license/helicopter_vB.bpmn",
                             customer_categories=["public", "gov"], default_version='a', a_hist_min_duration=1,
                             a_hist_max_duration=3)
    utils.post_bapol(utils.example_batch_policy)
    # create process instances/start the process x times
    currently_active_p_id = utils.get_currently_active_process_id()
    for i in range(10):
        response = utils.new_processes_instance(currently_active_p_id,
                                                utils.get_random_customer_category(["public", "gov"]))
        assert response.json().get("instantiated") is True
        assert "camundaInstanceId" in response.json().keys()

    assert utils.get_process_count() == 1
    assert utils.get_bapol_count() == 1
    assert utils.get_sum_of_instances(currently_active_p_id) == 10
    # TODO: check whether batch policy proposals are there
    # when
    utils.remove_all_process_rows()
    # then
    assert utils.get_process_count() == 0
    assert utils.get_bapol_count() == 0
    assert utils.get_sum_of_instances(currently_active_p_id) == 0
    # TODO: check whether batch policy proposals are deleted
