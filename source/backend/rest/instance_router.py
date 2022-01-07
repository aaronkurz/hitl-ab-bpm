from flask import Blueprint, request
from models import processes
from camunda.client import CamundaClient

instance_router_api = Blueprint('instance_router_api', __name__)


@instance_router_api.route('/start-instance', methods=['GET'])
def start_process():
    data = request.json

    process_id = int(request.args.get('process-id'))
    customer_category = request.args.get('customer-category')

    process = processes.get_process_metadata(process_id)

    # get rl env decision

    # give back running process on camunda id?

    client = CamundaClient()

    variant_a_camunda_id = process['variant_a_camunda_id']

    camunda_instance_id = client.start_instance(variant_a_camunda_id)

    return {"camunda_instance_id": camunda_instance_id}
