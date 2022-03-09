""" Unit tests regarding the process functionality """
from unittest.mock import MagicMock
import pytest
from models import process
from models.utils import Version
from models.process_instance import ProcessInstance
from models.batch_policy import BatchPolicy
from models import db
from rest.process import get_process_metadata, get_active_process_metadata

db.session = MagicMock()
pre_proc_var = MagicMock()
ProcessInstance.query = MagicMock()
BatchPolicy.query = MagicMock()
default_v = MagicMock(value='a')
proc_var = MagicMock(id=76,
                     datetime_added='2022-02-01',
                     interarrival_default_history=20.2,
                     experiment_state="running",
                     default_version=Version.A,
                     winning_reason=None,
                     datetime_decided=None)
expected = {
    'id': 76,
    'name': "test-proc",
    'customer_categories': 'gov-public',
    'datetime_added': "2022-02-01",
    'default_interarrival_time_history': 20.2,
    'experiment_state': "running",
    'default_version': "a",
    'winning_versions': None,
    'winning_reason': None,
    'datetime_decided': None,
    'number_batch_policies': 2,
    'number_instances': 157
}


@pytest.fixture(scope='module', autouse=True)
def before_all():
    """ Preparations

    Yields
    ------
    Nothing
        Nothing is yielded
    """
    proc_var.name = "test-proc"
    db.session.query.return_value.filter.return_value = pre_proc_var
    pre_proc_var.first.return_value = proc_var
    ProcessInstance.query.filter.return_value.count.return_value = 157
    BatchPolicy.query.filter.return_value.count.return_value = 2
    process.get_sorted_customer_category_list = MagicMock(return_value=['gov', 'public'])
    process.get_experiment_state_str = MagicMock(return_value='running')
    # ^ Will be executed before the first test
    yield
    # v Will be executed after the last test


def test_get_process_assertion_error_below():
    """ Check whether get_process_metadata raises error when there is no process """
    pre_proc_var.count.return_value = 0
    with pytest.raises(AssertionError):
        get_process_metadata(5)


def test_get_process_assertion_error_above():
    """ Check whether get_process_metadata raises error when there are two processes with corresponding id """
    pre_proc_var.count.return_value = 2
    with pytest.raises(AssertionError):
        get_process_metadata(5)


def test_get_process_valid():
    """ Check whether get_process_metadata returns expected result when there is one relevant process entry """
    pre_proc_var.count.return_value = 1

    assert get_process_metadata(5) == expected


def test_get_active_process_assertion_error_below():
    """ Check whether get_active_process_metadata raises error when there is no process """
    pre_proc_var.count.return_value = 0
    with pytest.raises(AssertionError):
        get_active_process_metadata()


def test_get_active_process_assertion_error_above():
    """ Check whether get_active_process_metadata raises error when there are two processes with corresponding id """
    pre_proc_var.count.return_value = 2
    with pytest.raises(AssertionError):
        get_active_process_metadata()


def test_get_active_process_valid():
    """ Check whether get_active_process_metadata returns expected result when there is one relevant process entry """
    pre_proc_var.count.return_value = 1
    assert get_active_process_metadata() == expected
