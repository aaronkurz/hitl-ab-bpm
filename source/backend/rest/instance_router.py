import requests
from flask import Blueprint, request, abort, jsonify
from models import processes
from instance_router import instance_router_interface
from models.process_instance import ProcessInstance
from sqlalchemy import and_
from matplotlib import pyplot as plt
import pandas as pd

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
@instance_router_api.route('/plt-cost', methods=['GET'])
def plt_cost():
    df = pd.read_csv('../instance_router/results/time_based_cost.csv')
    plt.plot(df[:])
    plt.xlabel('num_iterations', fontsize=14)
    plt.ylabel('time based cost(cost/milliseconds', fontsize=14)
    plt.legend(df.columns.values.tolist())
    return plt


CAMUNDA_ENGINE_URI = f"http://camunda:8080/engine-rest"

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
    # return Response(response=result['count'], status=200)
    print(result['count'])
    return {}

@instance_router_api.route('/get-batch-count', methods=['GET'])
def get_batch_count():
    history_url = '/history/batch/count'
    query_url = CAMUNDA_ENGINE_URI + history_url
    result = requests.get(query_url).json()
    print(result['count'])
    return {'batch_count':result['count']}

@instance_router_api.route('/get-process-count', methods=['GET'])
def get_process_count():
    history_url = '/history/process-instance/count'
    query_url = CAMUNDA_ENGINE_URI + history_url
    result = requests.get(query_url).json()
    return result['count']