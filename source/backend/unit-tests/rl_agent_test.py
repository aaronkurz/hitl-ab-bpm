import pytest
from unittest.mock import patch
from instance_router.private.rl_agent import get_reward


@pytest.fixture(scope='module', autouse=True)
def before_all():
    # ^ Will be executed before the first test
    yield
    # v Will be executed after the last test


def get_rounded_reward_2(duration: float):
    return round(get_reward(duration), 2)


@patch('config.K_QUANTILES_REWARD_FUNC', 20)
@patch('config.LOWER_CUTOFF_REWARD_FUNC', 0.2)
@patch('config.UPPER_CUTOFF_REWARD_FUNC', 0.8)
@patch('instance_router.private.rl_agent.quantiles', [0.021, 0.053, 0.06, 0.064, 0.068, 0.072, 0.075, 0.079, 0.082,
                                                      0.085, 0.09, 0.095, 0.102, 0.108, 0.117, 0.126, 0.14, 0.16057,
                                                      0.208, 0.314, 3.681])
def test_reward_func():
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
