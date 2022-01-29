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


def test_first_one_automatically_created():
    """ Test whether the first, naive bapol proposal is created for a new proposal """
    utils.post_processes_a_b("helicopter_license",
                             "./resources/bpmn/helicopter_license/helicopter_vA.bpmn",
                             "./resources/bpmn/helicopter_license/helicopter_vB.bpmn",
                             customer_categories=["public", "gov"],
                             default_version='a')
    assert utils.get_process_count() == 1
    params = {
        'process-id': utils.get_currently_active_process_id()
    }
    response = requests.get(BASE_URL + "/batch-policy-proposal/open", params=params)
    assert response.status_code == requests.codes.ok
    assert True is response.json().get('newProposalExists')

    # make sure the id is of the process just posted
    bapol_prop_process_id = response.json().get('proposal').get('processId')
    response_process_meta = requests.get(BASE_URL + "/process/active-meta")
    current_process_id = response_process_meta.json().get('id')
    assert current_process_id == bapol_prop_process_id

    # make sure there is no batch policy for proposal yet
    assert None is response.json().get('proposal').get('baPolId')



