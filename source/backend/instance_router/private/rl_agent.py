""" Here, the RL agent is implemented """
from models.process_instance import ProcessInstance
from models.batch_policy_proposal import BatchPolicyProposals
from sqlalchemy import and_


def learn_and_set_new_batch_policy_proposal(process_id: int):
    """

    :param process_id:
    :return: nothing
    """
    relevant_instances = ProcessInstance.query.filter(and_(ProcessInstance.process_id == process_id,
                                                           ProcessInstance.finished_time is not None,
                                                           ProcessInstance.do_evaluate is True,
                                                           ProcessInstance.reward is None))
    for instance in relevant_instances:
        relevant_instances.update(dict(reward=500, ))

    new_bpp = BatchPolicyProposals()
