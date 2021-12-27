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


@pytest.fixture(scope='session', autouse=True)
def after_all():
    # ^ Will be executed before the first test
    yield
    # v Will be executed after the last test
    assert requests.delete(BASE_URL + "/process-variants").status_code == requests.codes.OK


def test_set_process():
    """ Test if setting of new process with variants works """
    utils.set_processes_a_b("helicopter_license",
                            "./resources/bpmn/helicopter_license/helicopter_vA.bpmn",
                            "./resources/bpmn/helicopter_license/helicopter_vB.bpmn")
    assert requests.get(BASE_URL + "/process-variants/count").json().get("processesCount") == 1


def test_set_2_processes():
    """ Test if setting of new process with variants works """
    utils.set_processes_a_b("helicopter_license",
                            "./resources/bpmn/helicopter_license/helicopter_vA.bpmn",
                            "./resources/bpmn/helicopter_license/helicopter_vB.bpmn")
    utils.set_processes_a_b("helicopter_license_fast",
                            "./resources/bpmn/helicopter_license_fast/helicopter_fast_vA.bpmn",
                            "./resources/bpmn/helicopter_license_fast/helicopter_fast_vB.bpmn")
    assert requests.get(BASE_URL + "/process-variants/count").json().get("processesCount") == 2


def test_get_active_process_metadata():
    """ Test if receiving of metadata about currently active process works """
    # given
    test_set_2_processes()
    # when
    response = requests.get(BASE_URL + "/process-variants/active-meta")
    # then
    response_json = response.json()
    assert response.status_code == requests.codes.ok
    assert response_json.get("name") == "helicopter_license_fast"


def test_get_active_process_variants_files():
    # given
    test_set_2_processes()
    for version in ["a", "b"]:
        # given
        response_given = requests.get(BASE_URL + "/process-variants/active-meta")
        response_given_json = response_given.json()
        assert response_given.status_code == requests.codes.ok
        assert response_given_json.get("name") == "helicopter_license_fast"
        # when
        param = {"id": response_given_json.get("id")}
        response = requests.get(BASE_URL + "/process-variants/variant_file/" + version, params=param)
        # then
        assert response.headers['Content-Disposition'].split(";")[0] == "attachment"
        assert response.headers['Content-Disposition'].split(";")[1].split(".")[1] == "bpmn"

# TODO: test overwriting process
# TODO: check if files are deleted from filesystem after tests
