""" This module presents ways to interact with the instance router and its results from the outside """
from flask import Blueprint, request, abort
from sqlalchemy import and_, asc
import requests

from instance_router import instance_router_interface
from models import processes, db
from models.process_instance import ProcessInstance, TimeBasedCost, RewardOverIteration, ActionProbability
from models.processes import ProcessVariants
from rest.utils import validate_backend_process_id

instance_router_api = Blueprint('instance_router_api', __name__)


@instance_router_api.route('/start-instance', methods=['GET'])
def start_process():
    """ Endpoint for process consumers (clients) to request/start instances """
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
    """ Get some metadata about process """
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
    """ Get a time overview of client requests and where they have been routed to """
    process_id = request.args.get('process-id')
    validate_backend_process_id(process_id)

    all_instances_ordered = ProcessInstance.query.filter(ProcessInstance.process_id == process_id). \
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


# TODO: migrate RL script first
@instance_router_api.route('/time-based-cost', methods=['GET'])
def get_tbc():
    activity_list = request.args.get('actions')
    assert activity_list == TimeBasedCost.__table__.columns.keys()
    # ['Schedule', 'Eligibility Test', 'Medical Exam', 'Theory Test', 'Practical Test', 'Approve', 'Reject']
    # schedule_tbc = TimeBasedCost.query.filter(TimeBasedCost.columns.schedule_tbc)
    schedule_tbc = TimeBasedCost.columns.schedule_tbc
    elegibility_test_tbc = TimeBasedCost.columns.elegibility_test_tbc
    medical_test_tbc = TimeBasedCost.columns.medical_test_tbc
    theory_test_tbc = TimeBasedCost.columns.theory_test_tbc
    practical_test_tbc = TimeBasedCost.columns.practical_test_tbc
    approve_tbc = TimeBasedCost.columns.approve_tbc
    reject_tbc = TimeBasedCost.columns.reject_tbc

    return {
        'schedule_tbc': schedule_tbc,
        'elegibility_test_tbc': elegibility_test_tbc,
        'medical_test_tbc': medical_test_tbc,
        'theory_test_tbc': theory_test_tbc,
        'practical_test_tbc': practical_test_tbc,
        'approve_tbc': approve_tbc,
        'reject_tbc': reject_tbc,
    }


# TODO: migrate RL script first
@instance_router_api.route('/time-based-cost', methods=['POST'])
def store_tbc():
    activity_list = request.args.get('actions')
    assert activity_list == ['Schedule', 'Eligibility Test', 'Medical Exam', 'Theory Test', 'Practical Test', 'Approve',
                             'Reject']
    json = request.json
    schedule_tbc = json.get('schedule_tbc')
    elegibility_test_tbc = json.get('elegibility_test_tbc')
    medical_test_tbc = json.get('medical_test_tbc')
    theory_test_tbc = json.get('theory_test_tbc')
    practical_test_tbc = json.get('practical_test_tbc')
    approve_tbc = json.get('approve_tbc')
    reject_tbc = json.get('reject_tbc')
    tbc_over_new_iteration = TimeBasedCost(schedule_tbc=schedule_tbc,
                                           elegibility_test_tbc=elegibility_test_tbc,
                                           medical_test_tbc=medical_test_tbc,
                                           theory_test_tbc=theory_test_tbc,
                                           practical_test_tbc=practical_test_tbc,
                                           approve_tbc=approve_tbc,
                                           reject_tbc=reject_tbc)
    db.session.add(tbc_over_new_iteration)
    db.session.commit()
    return "Success"


# TODO: migrate RL script first
@instance_router_api.route('/action-prob', methods=['GET'])
def get_prob():
    variable_list = request.args.get('variable_list')
    assert variable_list == ['a', 'b']
    variant_a_prob = ActionProbability.columns.variant_a_prob
    variant_b_prob = ActionProbability.columns.variant_b_prob

    return {
        'variant_a_prob': variant_a_prob,
        'variant_b_prob': variant_b_prob
    }


# TODO: migrate RL script first
@instance_router_api.route('/action-prob', methods=['POST'])
def store_prob():
    variable_list = request.args.get('variable_list')
    assert variable_list == ['a', 'b']
    json = request.json
    variant_a_prob = json.get('variant_a_prob')
    variant_b_prob = json.get('variant_b_prob')

    prob_over_new_iteration = ActionProbability(variant_a_prob=variant_a_prob,
                                                variant_b_prob=variant_b_prob)
    db.session.add(prob_over_new_iteration)
    db.session.commit()
    return "Success"


# TODO: migrate RL script first
@instance_router_api.route('/reward', methods=['GET'])
def get_reward():
    reward = RewardOverIteration.columns.reward
    return {'reward': reward}


# TODO: migrate RL script first
@instance_router_api.route('/reward', methods=['POST'])
def store_reward():
    json = request.json
    reward = json.get('reward')
    reward = RewardOverIteration(reward=reward, )
    db.session.add(reward)
    db.session.commit()
    return "Success"


# TODO: add endpoint that returns plot of instantiations over time
# Return the Matplotlib image as a string/dict/request
# @instance_router_api.route('/plt-cost', methods=['GET'])
# def plt_cost():
#     df = pd.read_csv('./instance_router/results/time_based_cost.csv')
#     plt.plot(df[:])
#     plt.xlabel('num_iterations', fontsize=14)
#     plt.ylabel('time based cost(cost/milliseconds', fontsize=14)
#     plt.legend(df.columns.values.tolist())
#     # canvas = FigureCanvasAgg(plt)
#     # response = HttpResponse(content_type='image/png')
#     # canvas.print_png(response)
#     response = HttpResponse(content_type='image/png')
#     pylab.savefig(response, format="png")
#     return response

CAMUNDA_ENGINE_URI = f"http://camunda:8080/engine-rest"

@instance_router_api.route('/clean-up-history', methods=['POST'])
def clean_up_history():
    history_url = '/history/cleanup'
    query_url = CAMUNDA_ENGINE_URI + history_url
    requests.post(query_url)
    return "Success"


@instance_router_api.route('/fetch-history-activity-duration', methods=['GET'])
def fetch_history_activity_duration():
    history_url = '/history/activity-instance?'
    query_url = CAMUNDA_ENGINE_URI + history_url
    result = requests.get(query_url)
    history_activity_duration_dict = {}
    for instance in result.json():
        history_activity_duration_dict[instance['id']] = [instance['activityName'], instance['durationInMillis']]
    return history_activity_duration_dict


@instance_router_api.route('/get-activity-count', methods=['GET'])
def get_activity_count():
    history_url = '/history/activity-instance/count'
    query_url = CAMUNDA_ENGINE_URI + history_url
    result = requests.get(query_url).json()
    return {'activity_count': result['count']}


@instance_router_api.route('/get-batch-count', methods=['GET'])
def get_batch_count():
    history_url = '/history/batch/count'
    query_url = CAMUNDA_ENGINE_URI + history_url
    result = requests.get(query_url).json()
    print(result['count'])
    return {'batch_count': result['count']}


@instance_router_api.route('/get-process-count', methods=['GET'])
def get_process_count():
    history_url = '/history/process-instance/count'
    query_url = CAMUNDA_ENGINE_URI + history_url
    result = requests.get(query_url).json()
    return {'process_count': result['count']}
