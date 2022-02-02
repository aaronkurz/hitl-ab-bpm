""" Here, the RL agent is implemented """
from models.batch_policy_proposal import set_bapol_proposal


def learn_and_set_new_batch_policy_proposal(process_id: int):
    """

    :param process_id:
    :return: nothing
    """
    set_bapol_proposal(process_id, ["public", "gov"], [0.3, 0.5], [0.7, 0.5])
