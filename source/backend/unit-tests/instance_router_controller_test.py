import pytest
from unittest.mock import MagicMock, Mock
from models.process import Process, Version
from instance_router.private import controller


@pytest.fixture(scope='module', autouse=True)
def before_all():
    Process.query = MagicMock()
    # ^ Will be executed before the first test
    yield
    # v Will be executed after the last test


def test_get_winning_version_a():
    Process.query.filter.return_value.first.return_value = Mock(winning_version=Version.A)
    assert controller.get_winning_version(38) == 'a'


def test_get_winning_version_b():
    Process.query.filter.return_value.first.return_value = Mock(winning_version=Version.B)
    assert controller.get_winning_version(4) == 'b'


def test_get_winning_version_none():
    Process.query.filter.return_value.first.return_value = Mock(winning_version=None)
    assert controller.get_winning_version(121) is None
