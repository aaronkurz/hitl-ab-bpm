from flask import Blueprint, request, abort
from models import processes, db
from instance_router import instance_router_interface
from models.process_instance import ProcessInstance
from models.processes import ProcessVariants
from sqlalchemy import and_, asc
from rest.utils import validate_backend_process_id

instance_router_api = Blueprint('instance_router_api', __name__)


@instance_router_api.route('/start-instance', methods=['GET'])
def start_process():
    data = request.json

    process_id = int(request.args.get('process-id'))
    validate_backend_process_id(process_id)
    customer_category = request.args.get('customer-category')

    process = processes.get_process_metadata(process_id)

    # get decision from process bandit
    if not instance_router_interface.is_ready_for_instantiation():
        return {"instantiated": False,
                "message": "Server not ready for instantiation of processes. Try setting a process with two variants "
                           "and a learning-policy first."}
    camunda_instance_id = instance_router_interface.instantiate(process_id, customer_category)

    # return instance id (client does not need to know decision etc./maybe should
    # not even know they are part of an experiment)
    return {
        "instantiated": True,
        "camundaInstanceId": camunda_instance_id}


@instance_router_api.route('/aggregate-data', methods=['GET'])
def count_a_b():
    process_id = request.args.get('process-id')
    validate_backend_process_id(process_id)
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


@instance_router_api.route('/manual-decision', methods=['POST'])
def manual_decision():
    """ API endpoint to allow human expert to manually make a decision """
    process_id = request.args.get('process-id')
    validate_backend_process_id(process_id)
    decision = request.args.get('version-decision')
    if decision not in ['a', 'b']:
        abort(400, "version-decision query parameter must be 'a' or 'b'")
    process = ProcessVariants.query.filter(ProcessVariants.id == process_id).first()
    if process.winning_version is not None:
        abort(400, "This process already has a winning version")
    process.winning_version = decision
    db.session.commit()
    return "Success"


@instance_router_api.route('/aggregate-data/client-requests', methods=['GET'])
def get_instantiation_plot():
    process_id = request.args.get('process-id')
    validate_backend_process_id(process_id)

    all_instances_ordered = ProcessInstance.query.filter(ProcessInstance.process_id == process_id).\
        order_by(asc(ProcessInstance.instantiation_time))
    requests_a = []
    requests_b = []
    requests_a_counter = 0
    requests_b_counter = 0
    for instance in all_instances_ordered:
        if instance.decision == 'a':
            requests_a_counter += 1
        elif instance.decision == 'b':
            requests_b_counter += 1
        else:
            raise Exception("Unexpected decision for instance " + str(instance.id))

        requests_a.append(requests_a_counter)
        requests_b.append(requests_b_counter)

    return {
        "noTotalRequests": all_instances_ordered.count(),
        "requestsA": requests_a,
        "requestsB": requests_b
    }



