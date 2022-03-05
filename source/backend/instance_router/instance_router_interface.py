""" This is the main entry point to interact with the instance router from the outside """
# Just "fake" methods for now, in order to define an interface to connect the work that has been done
# on the RL side and the api/web-app side (has been kind if separate until now)
from instance_router.private import controller
from instance_router.private.controller import _fetch_and_learn
from models.process import get_experiment_state_enum
from models.utils import ExperimentState


def is_ready_for_instantiation() -> bool:
    """Check whether there is an active process and a batch/learning-policy and maybe other things.

    :return: True or False
    """
    return True


def instantiate(process_id: int, customer_category: str) -> dict:
    """ Returns either a or b

    :param process_id: specify process
    :param customer_category: specify customer category
    :return: 'a' or 'b'
    """
    instantiation_dict = controller.instantiate(process_id, customer_category)
    return instantiation_dict


def manual_fetch_and_learn(process_id: int):
    """Manually trigger fetching info about instances from camunda and training rl agent with this additional info

    :raises RuntimeWarning: Fetch and learn not possible due to experiment state
    (only possible in cool off and outside batch)
    :param process_id: specify process
    """
    exp_state = get_experiment_state_enum(process_id)
    if exp_state in [ExperimentState.IN_COOL_OFF, ExperimentState.COOL_OFF_FIN_DEC_OUTSTANDING]:
        _fetch_and_learn(process_id, in_cool_off_bool=True)
    elif exp_state == ExperimentState.RUNNING_OUTSIDE_BATCH:
        _fetch_and_learn(process_id, in_cool_off_bool=False)
    else:
        raise RuntimeWarning("Experiment state does not allow for manual fetch and learn.")
