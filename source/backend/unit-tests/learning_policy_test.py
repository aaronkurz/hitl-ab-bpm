from unittest.mock import MagicMock, Mock

import pytest

from models import db
from models.learning_policy import LearningPolicy, get_current_lepol, get_current_lepol_active_process

db.session = MagicMock()


@pytest.fixture(scope='module', autouse=True)
def before_all():
    exec_strat = Mock(customer_category="public",
                      exploration_probability_a=0.3,
                      exploration_probability_b=0.7)
    bapol = Mock(execution_strategies=[exec_strat, exec_strat],
                 last_modified="2020",
                 exp_length=200,
                 exp_decay=5,
                 process_id=5)
    LearningPolicy.query = MagicMock()
    LearningPolicy.query.order_by.return_value.filter.return_value.first.return_value = bapol
    # ^ Will be executed before the first test
    yield
    # v Will be executed after the last test


def test_get_current_bapol():
    assert {
               "experimentationLength": 200,
               "experimentationDecay": 5,
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
           } == get_current_lepol(5)


def test_active_count_zero():
    db.session.query.return_value.filter.return_value.count.return_value = 0
    with pytest.raises(Exception):
        get_current_lepol_active_process()


def test_active_count_too_many():
    db.session.query.return_value.filter.return_value.count.return_value = 2
    with pytest.raises(Exception):
        get_current_lepol_active_process()


def test_active_count_correct():
    db.session.query.return_value.filter.return_value.count.return_value = 1
    assert {
               "experimentationLength": 200,
               "experimentationDecay": 5,
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
           } == get_current_lepol_active_process()
