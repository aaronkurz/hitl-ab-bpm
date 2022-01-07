from flask import Blueprint, request, abort
from models import processes
from camunda.client import CamundaClient
from process_bandit import rl_env

instance_router_api = Blueprint('instance_router_api', __name__)


@instance_router_api.route('/start-instance', methods=['GET'])
def start_process():
    data = request.json

    process_id = int(request.args.get('process-id'))
    customer_category = request.args.get('customer-category')

    process = processes.get_process_metadata(process_id)

    # get decision from process bandit
    decision = rl_env.get_decision(process_id, customer_category)

    # instantiate according to decision
    client = CamundaClient()
    camunda_instance_id = None
    if decision == 'a':
        variant_a_camunda_id = process['variant_a_camunda_id']
        camunda_instance_id = client.start_instance(variant_a_camunda_id)
    elif decision == 'b':
        variant_a_camunda_id = process['variant_a_camunda_id']
        camunda_instance_id = client.start_instance(variant_a_camunda_id)
    else:
        abort(500, 'Unexpected decision by reinforcement learning environment')

    # return instance id
    return {"camunda_instance_id": camunda_instance_id}
