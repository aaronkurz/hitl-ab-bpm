""" Main "organizer" of instance routing """
from camunda.client import CamundaClient
from models import processes, db
from models.process_instance import ProcessInstance
from models.processes import ProcessVariants
from instance_router.private import process_bandit


def get_winning_version(process_id: int) -> str or None:
    """ In case the experiment is already done or a manual decision has been made, this will return that version

    :returns 'a' or 'b' or None
    """
    process = ProcessVariants.query.filter(ProcessVariants.id == process_id).first()
    if process.winning_version is not None:
        return process.winning_version
    else:
        return None


def instantiate(process_id: int, customer_category: str) -> str:
    """ Create a new process instance

    :param process_id: process id that we want to start
    :param customer_category: customer category of client
    :return: camunda instance id of started instance
    """
    process = processes.get_process_metadata(process_id)

    # get decision from process bandit, if no decision has been made yet
    winning_version = get_winning_version(process_id)
    if winning_version is None:
        decision = process_bandit.get_decision(process_id, customer_category)
    else:
        decision = winning_version

    # instantiate according to decision
    client = CamundaClient()
    if decision == 'a':
        variant_key = 'variant_a_camunda_id'
    elif decision == 'b':
        variant_key = 'variant_b_camunda_id'
    else:
        raise Exception('Unexpected decision by reinforcement learning environment')

    variant_camunda_id = process[variant_key]
    camunda_instance_id = client.start_instance(variant_camunda_id)
    # add info to database
    process_instance = ProcessInstance(process_id=process_id,
                                       decision=decision,
                                       camunda_instance_id=camunda_instance_id)
    db.session.add(process_instance)
    db.session.commit()

    # TODO schedule update of rewards

    return camunda_instance_id
