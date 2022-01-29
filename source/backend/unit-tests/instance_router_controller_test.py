from unittest.mock import MagicMock, Mock

import pytest

from instance_router.private import controller
from models.processes import ProcessVariants


@pytest.fixture(scope='module', autouse=True)
def before_all():
    ProcessVariants.query = MagicMock()
    # ^ Will be executed before the first test
    yield
    # v Will be executed after the last test


def test_get_winning_version_a():
    ProcessVariants.query.filter.return_value.first.return_value = Mock(winning_version='a')
    assert controller.get_winning_version(38) == 'a'


def test_get_winning_version_b():
    ProcessVariants.query.filter.return_value.first.return_value = Mock(winning_version='b')
    assert controller.get_winning_version(4) == 'b'


def test_get_winning_version_none():
    ProcessVariants.query.filter.return_value.first.return_value = Mock(winning_version=None)
    assert controller.get_winning_version(121) is None
