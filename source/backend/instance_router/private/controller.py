""" Main "organizer" of instance routing """
from random import randint
from typing import Optional
from threading import Lock
from sqlalchemy import and_
from camunda.client import CamundaClient
from instance_router.private import camunda_collector, rl_agent
from scipy.stats import bernoulli
from models import process, db
from models.process_instance import ProcessInstance, unevaluated_instances_still_exist
from models.batch_policy import append_process_instance_to_bapol
from models.batch_policy import get_average_batch_size
from models.process import Process, in_cool_off, is_in_batch
from models import batch_policy
from models.utils import Version

lock = Lock()


def get_winning_version(process_id: int, customer_category: str) -> Optional[Version] or None:
    """ In case the experiment is already done or a manual decision has been made, this will return that version

    :raises RuntimeError: Invalid customer category in instantiation request
    :param process_id: specify process
    :param customer_category: decision for which customer category
    :return: Version.A or Version.B or None
    """
    if not process.is_decision_made(process_id):
        return None
    for part_win in process.get_winning(process_id):
        if part_win['customer_category'] == customer_category:
            return part_win['winning_version']
    raise RuntimeError("Invalid customer category in instantiation request")


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
    """Get a decision to route if we are outside of the batch.

    :param process_id: process id
    :return: Version.A or Version.B
    """
    relevant_process = Process.query.filter(Process.id == process_id).first()
    return relevant_process.default_version


def end_of_batch_reached(process_id: int) -> bool:
    """Check whether we are at the end of the batch for a certain process (last instantiation request of batch).

    :param process_id: id of process
    :return: True or False
    """
    return ProcessInstance.query.filter(and_(ProcessInstance.process_id == process_id,
                                             ProcessInstance.do_evaluate.is_(True))).count() + 1 == \
           batch_policy.get_batch_size_sum(process_id)


def handle_decision_in_cool_off(process_id: int) -> Version:
    """Get routing decision and trigger collection from camunda and do reinforcement learning with new data

    :param process_id: specify process
    :return: Version.A or Version.B
    """
    decision = get_decision_outside_batch(process_id)
    # relearn with a probability of 1/avg_batch_size;
    # this means that when the average batch size was 15, will learn about
    # at about every 15th incoming instantiation request
    if _one_in_half_avg_batch_size_prob(process_id) and unevaluated_instances_still_exist(process_id):
        _fetch_and_learn(process_id, True)
    return decision


def _one_in_half_avg_batch_size_prob(process_id: int) -> bool:
    """Returns True with a probability of (one) in (half of average batch size) for a certain process

    :param process_id: process
    :return: True or False
    """
    half_batch_size = round(get_average_batch_size(process_id)/2)
    return half_batch_size == randint(0, half_batch_size)


def _fetch_and_learn(process_id: int, in_cool_off_bool: bool) -> None:
    """Fetch the newest data from camunda and do the learning and setting/updating of bapol proposal

    Thread-safe: only one thread can execute this method at the same time!
    Thread-safety necessary in case user triggers manual collection and learning while periodic collection and learning
    is underway.
    According to Python docs, in case it us currently locked, the next thread will wait:
    https://docs.python.org/3/library/asyncio-sync.html#asyncio.Lock.acquire
    :param process_id: specify process
    :param in_cool_off_bool: specify whether we are in cool-off
    """
    with lock:
        camunda_collector.collect_finished_instances(process_id)
        rl_agent.learn_and_set_new_batch_policy_proposal(process_id, in_cool_off=in_cool_off_bool)


def instantiate(process_id: int, customer_category: str) -> dict:
    """Create a new process instance.

    :raises RuntimeError: Illegal internal response; Unexpected decision by reinforcement learning environment
    :param process_id: process id that we want to start
    :param customer_category: customer category of client
    :return: camunda instance id of started instance
    """
    process_entry = process.get_process_entry(process_id)

    # get decision from process bandit, if no decision has been made yet
    winning_version = get_winning_version(process_id, customer_category)
    is_in_batch_marker = False
    if winning_version is None:
        if in_cool_off(process_id):
            # in cool-off period
            decision = handle_decision_in_cool_off(process_id)
        elif not is_in_batch(process_id):
            # in between batches
            decision = get_decision_outside_batch(process_id)
            if _one_in_half_avg_batch_size_prob(process_id) and unevaluated_instances_still_exist(process_id):
                # while an open proposal is ready for user, periodically update it to provide more info as
                # more instances finish and can be evaluated
                _fetch_and_learn(process_id, False)
        else:
            # is in batch
            is_in_batch_marker = True
            decision = get_decision_in_batch(process_id, customer_category)
            if end_of_batch_reached(process_id):
                _fetch_and_learn(process_id, False)
    else:
        decision = winning_version

    # instantiate according to decision
    client = CamundaClient()
    if decision == Version.A:
        variant_camunda_id = process_entry.variant_a_camunda_id
    elif decision == Version.B:
        variant_camunda_id = process_entry.variant_b_camunda_id
    else:
        raise RuntimeError('Unexpected decision by reinforcement learning environment: ' + str(decision))

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
        'camundaInstanceId': camunda_instance_id,
    }
