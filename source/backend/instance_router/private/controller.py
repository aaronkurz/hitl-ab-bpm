""" Main "organizer" of instance routing """
from random import randint
from sqlalchemy import and_
from camunda.client import CamundaClient
from instance_router.private import camunda_collector, rl_agent
from scipy.stats import bernoulli
from models import process, db
from models.process_instance import ProcessInstance, unevaluated_instances_still_exist
from models.batch_policy import append_process_instance_to_bapol
from models.batch_policy import get_average_batch_size
from models.process import Process, in_cool_off
from models import batch_policy
from models.utils import Version


def get_winning_version(process_id: int) -> Version or None:
    """ In case the experiment is already done or a manual decision has been made, this will return that version

    :returns Version.A or Version.B or None
    """
    relevant_process = Process.query.filter(Process.id == process_id).first()
    if relevant_process.winning_version is not None:
        return relevant_process.winning_version
    return None


def get_decision_in_batch(process_id: int, customer_category: str) -> Version:
    """ Will return the decision based on the currently active batch policy.
    :raises RuntimeError: Specified customer category not found in batch policy of process
    :param process_id: process id in backend
    :param customer_category: customer category of instantiation request
    :return: Version.A or Version.B
    """
    bapol_dict = batch_policy.get_current_bapol_data(process_id)
    for elem in bapol_dict.get('executionStrategy'):
        if elem.get('customerCategory') == customer_category:
            r_v = bernoulli(elem.get('explorationProbabilityB'))
            return [Version.A, Version.B][r_v.rvs(1)[0]]
            # rv.rvs(sample-size) will return either 0 or 1, and 1 with the probability of p in bernoulli(p)
    raise RuntimeError('No suitable customer category found in batch policy: ' + str(customer_category))


def get_decision_outside_batch(process_id: int) -> Version:
    """
    Get a decision to route if we are outside of the batch
   :param process_id: process id
   :return: Version.A or Version.B
   """
    relevant_process = Process.query.filter(Process.id == process_id).first()
    return relevant_process.default_version


def is_in_batch(process_id: int):
    """
    Check whether certain process experiment currently is in experimental batch
    :param process_id: process id
    :return: True or False
    """
    return ProcessInstance.query.filter(and_(ProcessInstance.process_id == process_id,
                                             ProcessInstance.do_evaluate.is_(True))).count() < \
           batch_policy.get_batch_size_sum(process_id)


def end_of_batch_reached(process_id: int):
    """
    Check whether we are at the end of the batch for a certain process (last instantiation request of batch)
    :param process_id: id of process
    :return: True or False
    """
    return ProcessInstance.query.filter(and_(ProcessInstance.process_id == process_id,
                                             ProcessInstance.do_evaluate.is_(True))).count() + 1 == \
           batch_policy.get_batch_size_sum(process_id)


def instantiate(process_id: int, customer_category: str) -> dict:
    """ Create a new process instance
    :raises RuntimeError: Illegal internal response; Unexpected decision by reinforcement learning environment
    :param process_id: process id that we want to start
    :param customer_category: customer category of client
    :return: camunda instance id of started instance
    """
    new_batch_policy_proposal_available = False
    process_metadata = process.get_process_metadata(process_id)

    # get decision from process bandit, if no decision has been made yet
    winning_version = get_winning_version(process_id)
    is_in_batch_marker = False
    if winning_version is None:
        if in_cool_off(process_id):
            decision = get_decision_outside_batch(process_id)
            # relearn with a probability of 1/avg_batch_size;
            # this means that when the average batch size was 15, will learn about
            # at about every 15th incoming instantiation request
            if round(get_average_batch_size(process_id)) == randint(0, round(get_average_batch_size(process_id))) \
                    and unevaluated_instances_still_exist(process_id):
                camunda_collector.collect_finished_instances(process_id)
                rl_agent.learn_and_set_new_batch_policy_proposal(process_id, in_cool_off=True)
        elif not is_in_batch(process_id):
            decision = get_decision_outside_batch(process_id)
            new_batch_policy_proposal_available = True
        else:
            is_in_batch_marker = True
            decision = get_decision_in_batch(process_id, customer_category)
            if end_of_batch_reached(process_id):
                camunda_collector.collect_finished_instances(process_id)
                rl_agent.learn_and_set_new_batch_policy_proposal(process_id, in_cool_off=False)
                new_batch_policy_proposal_available = True
    else:
        decision = winning_version

    # instantiate according to decision
    client = CamundaClient()
    if decision == Version.A:
        variant_key = 'variant_a_camunda_id'
    elif decision == Version.B:
        variant_key = 'variant_b_camunda_id'
    else:
        raise RuntimeError('Unexpected decision by reinforcement learning environment: ' + str(decision))

    variant_camunda_id = process_metadata[variant_key]
    camunda_instance_id = client.start_instance(variant_camunda_id)
    # add info to database
    if is_in_batch_marker:
        process_instance = ProcessInstance(process_id=process_id,
                                           decision=decision,
                                           camunda_instance_id=camunda_instance_id,
                                           customer_category=customer_category,
                                           do_evaluate=True)
        append_process_instance_to_bapol(process_id, process_instance)
    else:
        process_instance = ProcessInstance(process_id=process_id,
                                           decision=decision,
                                           camunda_instance_id=camunda_instance_id,
                                           customer_category=customer_category,
                                           do_evaluate=False)
    db.session.add(process_instance)
    db.session.commit()

    return {
        'newBatchPolicyProposalReady': new_batch_policy_proposal_available,
        'camundaInstanceId': camunda_instance_id,
    }
