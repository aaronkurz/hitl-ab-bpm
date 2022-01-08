from flask import Blueprint, request, abort, jsonify
from models import processes
from camunda.client import CamundaClient
from instance_router import instance_router_interface
from models.process_instance import ProcessInstance
from models import db
from sqlalchemy import and_

instance_router_api = Blueprint('instance_router_api', __name__)


@instance_router_api.route('/start-instance', methods=['GET'])
def start_process():
    data = request.json

    process_id = int(request.args.get('process-id'))
    customer_category = request.args.get('customer-category')

    process = processes.get_process_metadata(process_id)

    # get decision from process bandit
    if not instance_router_interface.is_ready_for_instantiation():
        return {"instantiated": False,
                "message": "Server not ready for instantiation of processes. Try setting a process with two variants "
                           "and a learning/batch-policy first."}
    camunda_instance_id = instance_router_interface.instantiate(process_id, customer_category)

    # return instance id (client does not need to know decision etc./maybe should
    # not even know they are part of an experiment)
    return {
        "instantiated": True,
        "camundaInstanceId": camunda_instance_id}


@instance_router_api.route('/aggregate-data', methods=['GET'])
def count_a_b():
    process_id = request.args.get('process-id')
    a_amount = ProcessInstance.query.filter(and_(ProcessInstance.process_id == process_id,
                                                 ProcessInstance.decision == 'a')).count()
    b_amount = ProcessInstance.query.filter(and_(ProcessInstance.process_id == process_id,
                                                 ProcessInstance.decision == 'b')).count()
    return {
        "a": {
            "amount": a_amount
        },
        "b": {
            "amount": b_amount
        }
        # TODO add further aggregated info, such as mean reward, percent finished and so on
    }

# TODO: add endpoint that returns plot of instantiations over time
