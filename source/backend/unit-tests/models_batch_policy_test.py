""" Test functions related to batch policy """
from unittest.mock import MagicMock, Mock
import pytest
from models.batch_policy import BatchPolicy, get_current_bapol_data, get_current_bapol_data_active_process
from models import db

db.session = MagicMock()


@pytest.fixture(scope='module', autouse=True)
def before_all():
    """ Preparations

    Yields
    ------
    Nothing
        Nothing is yielded
    """
    exec_strat = Mock(customer_category="public",
                      exploration_probability_a=0.3,
                      exploration_probability_b=0.7,)
    proposal = Mock(id=5)
    bapol = Mock(execution_strategies=[exec_strat, exec_strat],
                 time_added="2020",
                 batch_size=200,
                 process_id=5,
                 id=10,
                 batch_policy_proposal=proposal)
    BatchPolicy.query = MagicMock()
    BatchPolicy.query.filter.return_value.order_by.return_value.first.return_value = bapol
    # ^ Will be executed before the first test
    yield
    # v Will be executed after the last test


def test_get_current_bapol():
    """ Test whether get_current_bapol_data works as expected """
    assert {
               'baPolId': 10,
               'prevBaPolPropId': 5,
               "batchSize": 200,
               "lastModified": "2020",
               "processId": 5,
               "executionStrategy": [
                   {
                       "customerCategory": "public",
                       "explorationProbabilityA": 0.3,
                       "explorationProbabilityB": 0.7
                   },
                   {
                       "customerCategory": "public",
                       "explorationProbabilityA": 0.3,
                       "explorationProbabilityB": 0.7
                   }
               ]
           } == get_current_bapol_data(5)


def test_active_count_zero():
    """ Test whether get_current_bapol_data_active_process raises an exception when there is no batch policy """
    db.session.query.return_value.filter.return_value.count.return_value = 0
    with pytest.raises(Exception):
        get_current_bapol_data_active_process()


def test_active_count_too_many():
    """ Test whether get_current_bapol_data_active_process raises an exception when illegal state """
    db.session.query.return_value.filter.return_value.count.return_value = 2
    with pytest.raises(Exception):
        get_current_bapol_data_active_process()


def test_active_count_correct():
    """ Test whether get_current_bapol_data_active_process works as expected when exactly one bapol currently."""
    db.session.query.return_value.filter.return_value.count.return_value = 1
    assert {
               'baPolId': 10,
               'prevBaPolPropId': 5,
               "batchSize": 200,
               "lastModified": "2020",
               "processId": 5,
               "executionStrategy": [
                   {
                       "customerCategory": "public",
                       "explorationProbabilityA": 0.3,
                       "explorationProbabilityB": 0.7
                   },
                   {
                       "customerCategory": "public",
                       "explorationProbabilityA": 0.3,
                       "explorationProbabilityB": 0.7
                   }
               ]
           } == get_current_bapol_data_active_process()
