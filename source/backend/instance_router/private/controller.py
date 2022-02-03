""" Main "organizer" of instance routing """
from sqlalchemy import and_

from camunda.client import CamundaClient
from instance_router.private import camunda_collector
from scipy.stats import bernoulli
from models import process, db
from models.process_instance import ProcessInstance
from models.batch_policy import append_process_instance_to_bapol
from models.process import Process
from models import batch_policy
from instance_router.private import rl_agent


def get_winning_version(process_id: int) -> str or None:
    """ In case the experiment is already done or a manual decision has been made, this will return that version

    :returns 'a' or 'b' or None
    """
    relevant_process = Process.query.filter(Process.id == process_id).first()
    if relevant_process.winning_version is not None:
        return relevant_process.winning_version.value
    else:
        return None


def get_decision_in_batch(process_id, customer_category) -> str:
    """
   :param process_id:
   :param customer_category:
   :return: 'a' or 'b'
   """
    bapol_dict = batch_policy.get_current_bapol_data(process_id)
    for elem in bapol_dict.get('executionStrategy'):
        if elem.get('customerCategory') == customer_category:
            return ['a', 'b'][bernoulli.rvs(elem.get('explorationProbabilityB'))]
            # bernoulli.rvs(p) will return either 0 or 1, and 1 with the probability of p
    raise Exception('No suitable customer category found in batch policy: ' + str(customer_category))


def get_decision_outside_batch(process_id) -> str:
    """
   :param process_id:
   :return: 'a' or 'b'
   """
    relevant_process = Process.query.filter(Process.id == process_id).first()
    return relevant_process.default_version.value


def is_in_batch(process_id):
    return ProcessInstance.query.filter(and_(ProcessInstance.process_id == process_id,
                                             ProcessInstance.do_evaluate == True)).count() <\
           batch_policy.get_batch_size_sum(process_id)


def end_of_batch_reached(process_id):
    return ProcessInstance.query.filter(and_(ProcessInstance.process_id == process_id,
                                             ProcessInstance.do_evaluate == True)).count() + 1 ==\
           batch_policy.get_batch_size_sum(process_id)


def instantiate(process_id: int, customer_category: str) -> dict:
    """ Create a new process instance

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
        if not is_in_batch(process_id):
            decision = get_decision_outside_batch(process_id)
            new_batch_policy_proposal_available = True
        else:
            is_in_batch_marker = True
            decision = get_decision_in_batch(process_id, customer_category)
            if end_of_batch_reached(process_id):
                camunda_collector.collect_finished_instances(process_id)
                rl_agent.learn_and_set_new_batch_policy_proposal(process_id)
                new_batch_policy_proposal_available = True
    else:
        decision = winning_version

    # instantiate according to decision
    client = CamundaClient()
    if decision == 'a':
        variant_key = 'variant_a_camunda_id'
    elif decision == 'b':
        variant_key = 'variant_b_camunda_id'
    else:
        raise Exception('Unexpected decision by reinforcement learning environment: ' + str(decision))

    variant_camunda_id = process_metadata[variant_key]
    camunda_instance_id = client.start_instance(variant_camunda_id)
    # add info to database
    if is_in_batch_marker:
        process_instance = ProcessInstance(process_id=process_id,
                                           decision=decision,
                                           camunda_instance_id=camunda_instance_id,
                                           do_evaluate=True)
        append_process_instance_to_bapol(process_id, process_instance)
    else:
        process_instance = ProcessInstance(process_id=process_id,
                                           decision=decision,
                                           camunda_instance_id=camunda_instance_id,
                                           do_evaluate=False)
    db.session.add(process_instance)
    db.session.commit()

    return {
        'newBatchPolicyProposalReady': new_batch_policy_proposal_available,
        'camundaInstanceId': camunda_instance_id,
    }
