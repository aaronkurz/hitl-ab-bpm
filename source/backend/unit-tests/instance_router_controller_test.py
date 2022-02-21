""" Unit tests regarding the instance router controller """
from unittest.mock import MagicMock, Mock
import pytest
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
    Process.query.filter.return_value.first.return_value = Mock(winning_version=Version.A)
    assert controller.get_winning_version(38) == Version.A


def test_get_winning_version_b():
    """ Check whether it returns winning version b when expected """
    Process.query.filter.return_value.first.return_value = Mock(winning_version=Version.B)
    assert controller.get_winning_version(4) == Version.B


def test_get_winning_version_none():
    """ Check whether it returns winning version None when expected """
    Process.query.filter.return_value.first.return_value = Mock(winning_version=None)
    assert controller.get_winning_version(121) is None
