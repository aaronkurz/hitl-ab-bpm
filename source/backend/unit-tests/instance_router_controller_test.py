""" Unit tests regarding the instance router controller """
from unittest.mock import MagicMock
import pytest
from models import process
from models.process import Process
from models.utils import Version
from instance_router.private import controller


@pytest.fixture(scope='module', autouse=True)
def before_all():
    """ Preparations

    Yields
    ------
    Nothing
        Nothing is yielded
    """
    Process.query = MagicMock()
    # ^ Will be executed before the first test
    yield
    # v Will be executed after the last test


def test_get_winning_version_a():
    """ Check whether it returns winning version a when expected """
    decision_list = [dict(customer_category="public", winning_version=Version.A)]
    process.get_winning = MagicMock(return_value=decision_list)
    process.is_decision_made = MagicMock(return_value=True)
    assert controller.get_winning_version(38, "public") == Version.A


def test_get_winning_version_b():
    """ Check whether it returns winning version b when expected """
    decision_list = [dict(customer_category="gov", winning_version=Version.B)]
    process.get_winning = MagicMock(return_value=decision_list)
    process.is_decision_made = MagicMock(return_value=True)
    assert controller.get_winning_version(4, "gov") == Version.B


def test_get_winning_version_none():
    """ Check whether it returns winning version None when expected """
    process.is_decision_made = MagicMock(return_value=False)
    assert controller.get_winning_version(121, "public") is None
