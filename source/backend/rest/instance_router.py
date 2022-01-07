from flask import Blueprint, request, abort, jsonify
from models import processes
from camunda.client import CamundaClient
from process_bandit import process_bandit
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

    # add info to database
    process_instance = ProcessInstance(process_id=process_id,
                                       decision=decision,
                                       camunda_instance_id=camunda_instance_id)
    db.session.add(process_instance)
    db.session.commit()

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
