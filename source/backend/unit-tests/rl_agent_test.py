""" Unit tests regarding rl agent """
from unittest.mock import patch
import pytest
from datetime import datetime
from instance_router.private.rl_agent import get_reward, to_vw_format, get_action_prob_per_context_dict, calculate_duration


@pytest.fixture(scope='module', autouse=True)
def before_all():
    """ Preparations

    Yields
    ------
    Nothing
        Nothing is yielded
    """
    # ^ Will be executed before the first test
    yield
    # v Will be executed after the last test


def get_rounded_reward_2(duration: float) -> float:
    """ Helper function to round reward.

    :param duration: not rounded duration
    :return: rounded duration, two decimal points
    """
    return round(get_reward(duration), 2)


@patch('config.K_QUANTILES_REWARD_FUNC', 20)
@patch('config.LOWER_CUTOFF_REWARD_FUNC', 0.2)
@patch('config.UPPER_CUTOFF_REWARD_FUNC', 0.8)
@patch('instance_router.private.rl_agent.rl_agent_globals', dict(latest_process_id=1,
                                                                 vw=None,
                                                                 quantiles=[0.021, 0.053, 0.06, 0.064,
                                                                            0.068, 0.072, 0.075, 0.079,
                                                                            0.082,0.085, 0.09, 0.095,
                                                                            0.102, 0.108, 0.117, 0.126,
                                                                            0.14, 0.16057, 0.208, 0.314, 3.681]))
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

def test_retrieval_of_agent_information():
    """ Check if the probabilities for any given action under given context are correctly retrieved"""

def test_duration_func():
    """ Test if the duration is properly calculated"""
    start_time = datetime.strptime('01/01/2019 01:21:00', '%d/%m/%Y %I:%M:%S')
    end_time = datetime.strptime('01/01/2019 01:21:01', '%d/%m/%Y %I:%M:%S')
    assert calculate_duration(start_time, end_time) == 1.0

    start_time = datetime.strptime('02/01/2019 01:21:00', '%d/%m/%Y %I:%M:%S')
    end_time = datetime.strptime('01/01/2019 01:21:01', '%d/%m/%Y %I:%M:%S')
    assert calculate_duration(start_time, end_time) == -86399.0



