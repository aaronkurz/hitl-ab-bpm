import pytest
from unittest.mock import MagicMock, Mock
from models.processes import get_process_metadata, get_active_process_metadata
from models import db

db.session = MagicMock()
pre_proc_var = MagicMock()
proc_var = MagicMock(id=76,
                     variant_a_path="/path/to/a",
                     variant_b_path="/path/to/b",
                     variant_a_camunda_id="id1",
                     variant_b_camunda_id="id2",
                     winning_version=None)
expected = {
        'id': 76,
        'name': "taxi-request",
        'variant_a_path': "/path/to/a",
        'variant_b_path': "/path/to/b",
        'variant_a_camunda_id': "id1",
        'variant_b_camunda_id': "id2",
        'winning_version': None
    }


@pytest.fixture(scope='module', autouse=True)
def before_all():
    proc_var.name = "taxi-request"
    db.session.query.return_value.filter.return_value = pre_proc_var
    pre_proc_var.first.return_value = proc_var
    # ^ Will be executed before the first test
    yield
    # v Will be executed after the last test


def test_get_process_assertion_error_below():
    pre_proc_var.count.return_value = 0
    with pytest.raises(AssertionError):
        get_process_metadata(5)


def test_get_process_assertion_error_above():
    pre_proc_var.count.return_value = 2
    with pytest.raises(AssertionError):
        get_process_metadata(5)


def test_get_process_valid():
    pre_proc_var.count.return_value = 1
    assert expected == get_process_metadata(5)


def test_get_active_process_assertion_error_below():
    pre_proc_var.count.return_value = 0
    with pytest.raises(AssertionError):
        get_active_process_metadata()


def test_get_active_process_assertion_error_above():
    pre_proc_var.count.return_value = 2
    with pytest.raises(AssertionError):
        get_active_process_metadata()


def test_get_active_process_valid():
    pre_proc_var.count.return_value = 1
    assert expected == get_active_process_metadata()


