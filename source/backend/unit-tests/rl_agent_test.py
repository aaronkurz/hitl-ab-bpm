""" Unit tests regarding rl agent """
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import pytest
import vowpalwabbit
from instance_router.private.rl_agent import get_reward, to_vw_format, learn_and_set_new_batch_policy_proposal, \
    calculate_duration
from models import db
from models.process_instance import ProcessInstance
from models.utils import Version


@pytest.fixture(scope='module', autouse=True)
def before_all():
    """ Preparations

    Yields
    ------
    Nothing
        Nothing is yielded
    """
    ProcessInstance.query = MagicMock()
    db.session = MagicMock()
    # ^ Will be executed before the first test
    yield
    # v Will be executed after the last test


def create_mock_process_instance_list(times: int,
                                      version: Version,
                                      duration_seconds: float,
                                      customer_category: str) -> list:
    """Create a list of mocked process instances for mocking of database

    :param times: how many mocked process instances should be created
    :param version: Version.A or Version.B
    :param duration_seconds: How long the instances should take
    :param customer_category: Which customer category
    :return: List containing all the mocked instances
    """
    start_time = datetime.strptime('01/01/2019 01:21:00', '%d/%m/%Y %I:%M:%S')
    end_time = start_time + timedelta(seconds=duration_seconds)
    m_list = []
    for _ in range(times):
        m_list.append(MagicMock(instantiation_time=start_time,
                                finished_time=end_time,
                                decision=version,
                                customer_category=customer_category))
    return m_list


def get_rounded_reward_2(duration: float) -> float:
    """ Helper function to round reward.

    :param duration: not rounded duration
    :return: rounded duration, two decimal points
    """
    return round(get_reward(duration), 2)


@patch('config.K_QUANTILES_REWARD_FUNC', 20)
@patch('config.LOWER_CUTOFF_REWARD_FUNC', 0.2)
@patch('config.UPPER_CUTOFF_REWARD_FUNC', 0.8)
@patch('instance_router.private.rl_agent.rl_agent_globals', {"latest_process_id": 1,
                                                             "vw": None,
                                                             "quantiles": [0.021, 0.053, 0.06, 0.064,
                                                                           0.068, 0.072, 0.075, 0.079,
                                                                           0.082, 0.085, 0.09, 0.095,
                                                                           0.102, 0.108, 0.117, 0.126,
                                                                           0.14, 0.16057, 0.208, 0.314, 3.681]})
def test_reward_func():
    """ Check if reward function behaves as expected """
    assert get_rounded_reward_2(0.020) == 1.0
    assert get_rounded_reward_2(0.021) == 0.77
    assert get_rounded_reward_2(0.029) == 0.77
    assert get_rounded_reward_2(0.055) == 0.74
    assert get_rounded_reward_2(0.062) == 0.71
    assert get_rounded_reward_2(0.064) == 0.68
    assert get_rounded_reward_2(0.069) == 0.65
    assert get_rounded_reward_2(0.073) == 0.62
    assert get_rounded_reward_2(0.077) == 0.59
    assert get_rounded_reward_2(0.080) == 0.56
    assert get_rounded_reward_2(0.083) == 0.53
    assert get_rounded_reward_2(0.087) == 0.50
    assert get_rounded_reward_2(0.091) == 0.47
    assert get_rounded_reward_2(0.096) == 0.44
    assert get_rounded_reward_2(0.104) == 0.41
    assert get_rounded_reward_2(0.1094) == 0.38
    assert get_rounded_reward_2(0.118) == 0.35
    assert get_rounded_reward_2(0.128) == 0.32
    assert get_rounded_reward_2(0.1563) == 0.29
    assert get_rounded_reward_2(0.1615) == 0.26
    assert get_rounded_reward_2(0.22) == 0.23
    assert get_rounded_reward_2(0.32) == 0.2
    assert get_rounded_reward_2(3.681) == 0.0
    assert get_rounded_reward_2(5.3) == 0.0


def test_vw_format_transformation():
    """ Check if the strings are correctly transformed into the required vw format"""
    string_1 = to_vw_format({'orga': 'public'}, ['A', 'B'], ('A', 0.5, 0.5))
    assert string_1 == 'shared |Orga orga=public\n0:0.5:0.5 |Action variant=A \n|Action variant=B '
    string_2 = to_vw_format({'orga': 'ngo'}, ['A', 'B'], ('B', 0.5, 0.8))
    assert string_2 == 'shared |Orga orga=ngo\n|Action variant=A \n0:0.5:0.8 |Action variant=B '


@patch('instance_router.private.rl_agent.rl_agent_globals', {"latest_process_id": 76,
                                                             "vw": vowpalwabbit.Workspace('--cb_explore_adf -q UA '
                                                                                           '--rnd 3 --epsilon 0.025',
                                                                                           quiet=True),
                                                             "quantiles": [0.021, 0.053, 0.06, 0.064,
                                                                           0.068, 0.072, 0.075, 0.079,
                                                                           0.082, 0.085, 0.09, 0.095,
                                                                           0.102, 0.108, 0.117, 0.126,
                                                                           0.14, 0.16057, 0.208, 0.314, 3.681]})
@patch('instance_router.private.rl_agent.get_sorted_customer_category_list')
@patch('instance_router.private.rl_agent.set_or_update_bapol_proposal')
def test_learn_and_set_new_bpp_different_ab_perf_cc(patch_set_or_update_bapol_proposal: MagicMock,
                                                    patch_get_sorted_customer_category_list: MagicMock):
    """  Check if the probabilities for any given action under given context are correctly retrieved

    Test with different performance of versions for customer categories:
    test a is more likely to be called for government than for public
    test b is more likely to be called for public than for government
    :param patch_set_or_update_bapol_proposal:
    :param patch_get_sorted_customer_category_list:
    """
    mock_instance_list = []
    mock_instance_list.extend(create_mock_process_instance_list(times=15,
                                                                version=Version.A,  # for gov, a is better
                                                                duration_seconds=2,
                                                                customer_category="gov"))
    mock_instance_list.extend(create_mock_process_instance_list(times=15,
                                                                version=Version.B,
                                                                duration_seconds=20,
                                                                customer_category="gov"))
    mock_instance_list.extend(create_mock_process_instance_list(times=15,
                                                                version=Version.B,  # for public, b is better
                                                                duration_seconds=2,
                                                                customer_category="public"))
    mock_instance_list.extend(create_mock_process_instance_list(times=15,
                                                                version=Version.A,
                                                                duration_seconds=20,
                                                                customer_category="public"))
    ProcessInstance.query.filter.return_value = mock_instance_list
    patch_get_sorted_customer_category_list.return_value = ["gov", "public"]
    learn_and_set_new_batch_policy_proposal(76, False)
    patch_set_or_update_bapol_proposal.assert_called_once()
    call_args = patch_set_or_update_bapol_proposal.call_args[0]
    assert call_args[0] == 76
    assert call_args[1] == ["gov", "public"]
    # test a is more likely to be called for government than for public
    assert call_args[2][0] < call_args[2][1]
    # test b is more likely to be called for public than for government
    assert call_args[3][0] > call_args[3][1]


@patch('instance_router.private.rl_agent.rl_agent_globals', {"latest_process_id": 76,
                                                             "vw": vowpalwabbit.Workspace('--cb_explore_adf -q UA '
                                                                                           '--rnd 3 --epsilon 0.025',
                                                                                           quiet=True),
                                                             "quantiles": [0.021, 0.053, 0.06, 0.064,
                                                                           0.068, 0.072, 0.075, 0.079,
                                                                           0.082, 0.085, 0.09, 0.095,
                                                                           0.102, 0.108, 0.117, 0.126,
                                                                           0.14, 0.16057, 0.208, 0.314, 3.681]})
@patch('instance_router.private.rl_agent.get_sorted_customer_category_list')
@patch('instance_router.private.rl_agent.set_or_update_bapol_proposal')
def test_learn_and_set_new_bpp_same_ab_perf_cc(patch_set_or_update_bapol_proposal: MagicMock,
                                                                 patch_get_sorted_customer_category_list: MagicMock):
    """  Check if the probabilities for any given action under given context are correctly retrieved

    A should be better than B for both customer categories
    :param patch_set_or_update_bapol_proposal:
    :param patch_get_sorted_customer_category_list:
    """
    mock_instance_list = []
    mock_instance_list.extend(create_mock_process_instance_list(times=15,
                                                                version=Version.A,  # for gov, a is better
                                                                duration_seconds=2,
                                                                customer_category="gov"))
    mock_instance_list.extend(create_mock_process_instance_list(times=15,
                                                                version=Version.B,
                                                                duration_seconds=20,
                                                                customer_category="gov"))
    mock_instance_list.extend(create_mock_process_instance_list(times=15,
                                                                version=Version.A,  # for public, a is better
                                                                duration_seconds=2,
                                                                customer_category="public"))
    mock_instance_list.extend(create_mock_process_instance_list(times=15,
                                                                version=Version.B,
                                                                duration_seconds=20,
                                                                customer_category="public"))
    ProcessInstance.query.filter.return_value = mock_instance_list
    patch_get_sorted_customer_category_list.return_value = ["gov", "public"]
    learn_and_set_new_batch_policy_proposal(76, False)
    patch_set_or_update_bapol_proposal.assert_called_once()
    call_args = patch_set_or_update_bapol_proposal.call_args[0]
    assert call_args[0] == 76
    assert call_args[1] == ["gov", "public"]
    # test a
    assert call_args[2][0] > 0.6
    assert call_args[3][0] < 0.4
    # test b
    assert call_args[2][1] > 0.6
    assert call_args[3][1] < 0.4


def test_duration_func():
    """ Test if the duration is properly calculated"""
    start_time = datetime.strptime('01/01/2019 01:21:00', '%d/%m/%Y %I:%M:%S')
    end_time = datetime.strptime('01/01/2019 01:21:01', '%d/%m/%Y %I:%M:%S')
    assert calculate_duration(start_time, end_time) == 1.0

    start_time = datetime.strptime('02/01/2019 01:21:00', '%d/%m/%Y %I:%M:%S')
    end_time = datetime.strptime('01/01/2019 01:21:01', '%d/%m/%Y %I:%M:%S')
    assert calculate_duration(start_time, end_time) == -86399.0
