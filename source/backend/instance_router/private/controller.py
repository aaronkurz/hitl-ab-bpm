from camunda.client import CamundaClient
from models import processes, db
from models.process_instance import ProcessInstance
from instance_router.private import process_bandit


def instantiate(process_id: int, customer_category: str) -> str:
    process = processes.get_process_metadata(process_id)

    # get decision from process bandit
    decision_process_bandit = process_bandit.get_decision(process_id, customer_category)

    # instantiate according to decision
    client = CamundaClient()
    variant_key = None
    if decision_process_bandit == 'a':
        variant_key = 'variant_a_camunda_id'
    elif decision_process_bandit == 'b':
        variant_key = 'variant_b_camunda_id'
    else:
        raise Exception('Unexpected decision by reinforcement learning environment')

    variant_camunda_id = process[variant_key]
    camunda_instance_id = client.start_instance(variant_camunda_id)
    # add info to database
    process_instance = ProcessInstance(process_id=process_id,
                                       decision=decision_process_bandit,
                                       camunda_instance_id=camunda_instance_id)
    db.session.add(process_instance)
    db.session.commit()

    # TODO schedule update of rewards

    return camunda_instance_id
