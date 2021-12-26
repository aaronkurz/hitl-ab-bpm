import pytest
import requests
from config import BASE_URL


@pytest.fixture(autouse=True)
def run_before_each_test():
    assert requests.delete(BASE_URL + "/process-variants").status_code == requests.codes.OK
    # ^ before test
    yield
    # v after test


def test_set_process():
    """ Test if setting of new process with variants works """
    # given
    files_in = {
        "variantA": open("./resources/bpmn/helicopter_license/helicopter_vA.bpmn"),
        "variantB": open("./resources/bpmn/helicopter_license/helicopter_vB.bpmn")
    }
    # when
    response = requests.post(BASE_URL + "/process-variants/helicopter_license", files=files_in)
    # then
    assert response.status_code == requests.codes.ok
    assert requests.get(BASE_URL + "/process-variants/count").json().get("processesCount") == 1


def test_set_2_processes():
    """ Test if setting of new process with variants works """
    # given
    test_set_process()
    files_in = {
        "variantA": open("./resources/bpmn/helicopter_license_fast/helicopter_fast_vA.bpmn"),
        "variantB": open("./resources/bpmn/helicopter_license_fast/helicopter_fast_vB.bpmn")
    }
    # when
    response = requests.post(BASE_URL + "/process-variants/helicopter_license_fast", files=files_in)
    # then
    assert response.status_code == requests.codes.ok
    assert requests.get(BASE_URL + "/process-variants/count").json().get("processesCount") == 2
