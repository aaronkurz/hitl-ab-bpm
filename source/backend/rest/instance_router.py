from flask import Blueprint, request, abort
from models import processes
from camunda.client import CamundaClient
from process_bandit import process_bandit

instance_router_api = Blueprint('instance_router_api', __name__)


@instance_router_api.route('/start-instance', methods=['GET'])
def start_process():
    data = request.json

    process_id = int(request.args.get('process-id'))
    customer_category = request.args.get('customer-category')

    process = processes.get_process_metadata(process_id)

    # get decision from process bandit
    if not process_bandit.is_ready_for_decision():
        return {"instantiated": False,
                "message": "Server not ready for instantiation of processes. Try setting a process with two variants "
                           "and a learning/batch-policy first."}
    decision = process_bandit.get_decision(process_id, customer_category)

    # instantiate according to decision
    client = CamundaClient()
    variant_key = None
    if decision == 'a':
        variant_key = 'variant_a_camunda_id'
    elif decision == 'b':
        variant_key = 'variant_b_camunda_id'
    else:
        abort(500, 'Unexpected decision by reinforcement learning environment')

    variant_a_camunda_id = process[variant_key]
    camunda_instance_id = client.start_instance(variant_a_camunda_id)
    # TODO: write decision in database

    # return instance id
    return {
        "instantiated": True,
        "camunda_instance_id": camunda_instance_id}


# TODO: API endpoints to retrieve decision history
