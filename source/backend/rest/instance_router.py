""" This module presents rest endpoints to interact with the instance router and its results from the outside """
import statistics
from flask import Blueprint, request, abort
from instance_router import instance_router_interface
from models.batch_policy import BatchPolicy
from models.process import is_valid_customer_category
from models.process_instance import ProcessInstance
from models.utils import Version
from sqlalchemy import and_, asc
from rest.utils import validate_backend_process_id

instance_router_api = Blueprint('instance_router_api', __name__)


@instance_router_api.route('/start-instance', methods=['GET'])
# pylint: disable=missing-return-doc, missing-return-type-doc
def start_process():
    """ Endpoint for process consumers (clients) to request/start instances """
    process_id = int(request.args.get('process-id'))
    validate_backend_process_id(process_id)
    customer_category = request.args.get('customer-category')
    if not is_valid_customer_category(process_id, customer_category):
        abort(400, "Not a valid customer category")

    # get decision from process bandit
    if not instance_router_interface.is_ready_for_instantiation():
        return {"instantiated": False,
                "message": "Server not ready for instantiation of processes. Try setting a process with two variants "
                           "and a learning-policy first."}
    instantiation_dict = instance_router_interface.instantiate(process_id, customer_category)

    # return instance id (client does not need to know decision etc./maybe should
    # not even know they are part of an experiment)
    return {
        "instantiated": True,
        "camundaInstanceId": instantiation_dict.get('camundaInstanceId')
    }


@instance_router_api.route('/aggregate-data', methods=['GET'])
# pylint: disable=missing-return-doc, missing-return-type-doc
def count_a_b():
    """Get some metadata about process: all data concerns only the instances that were part of an experimental batch!"""
    process_id = request.args.get('process-id')
    validate_backend_process_id(process_id)
    relevant_queries_ab = {
        Version.A: ProcessInstance.query.filter(and_(ProcessInstance.process_id == process_id,
                                                     ProcessInstance.decision == Version.A,
                                                     ProcessInstance.do_evaluate.is_(True))),
        Version.B: ProcessInstance.query.filter(and_(ProcessInstance.process_id == process_id,
                                                     ProcessInstance.decision == Version.B,
                                                     ProcessInstance.do_evaluate.is_(True)))}

    number_started_ab = {
        Version.A: relevant_queries_ab[Version.A].count(),
        Version.B: relevant_queries_ab[Version.B].count()}

    all_relevant_query_finished_ab = {
        Version.A: relevant_queries_ab[Version.A].filter(ProcessInstance.finished_time.is_not(None)),
        Version.B: relevant_queries_ab[Version.B].filter(ProcessInstance.finished_time.is_not(None))}

    # Test if reward was calculated for all finished instances in batches, as expected
    assert all_relevant_query_finished_ab[Version.A].count() == relevant_queries_ab[Version.A] \
        .filter(ProcessInstance.reward.is_not(None)).count() \
           and all_relevant_query_finished_ab[Version.B].count() == relevant_queries_ab[Version.B] \
               .filter(ProcessInstance.reward.is_not(None)).count(), \
        "Server Error: Reward was not calculated properly for all finished instances"

    a_number_finished = all_relevant_query_finished_ab[Version.A].count()
    b_number_finished = all_relevant_query_finished_ab[Version.B].count()

    a_list_durations = [(instance.finished_time - instance.instantiation_time).total_seconds()
                        for instance in all_relevant_query_finished_ab[Version.A]]
    b_list_durations = [(instance.finished_time - instance.instantiation_time).total_seconds()
                        for instance in all_relevant_query_finished_ab[Version.B]]
    a_average_duration_sec = None if len(a_list_durations) == 0 else statistics.mean(a_list_durations)
    b_average_duration_sec = None if len(b_list_durations) == 0 else statistics.mean(b_list_durations)

    a_list_rew = [instance.reward for instance in all_relevant_query_finished_ab[Version.A]]
    b_list_rew = [instance.reward for instance in all_relevant_query_finished_ab[Version.B]]
    a_average_reward = None if len(a_list_rew) == 0 else statistics.mean(a_list_rew)
    b_average_reward = None if len(b_list_rew) == 0 else statistics.mean(b_list_rew)

    return {
        "a": {
            "numberStarted": number_started_ab[Version.A],
            "numberFinished": a_number_finished,
            "averageDurationSec": a_average_duration_sec,
            "averageReward": a_average_reward
        },
        "b": {
            "numberStarted": number_started_ab[Version.B],
            "numberFinished": b_number_finished,
            "averageDurationSec": b_average_duration_sec,
            "averageReward": b_average_reward
        }
    }


@instance_router_api.route('/aggregate-data/client-requests', methods=['GET'])
# pylint: disable=missing-return-doc, missing-return-type-doc
def get_instantiation_data():
    """ Get a time overview of client requests and where they have been routed to (in batch) """
    process_id = int(request.args.get('process-id'))
    validate_backend_process_id(process_id)

    all_instances_ordered = ProcessInstance.query.filter(and_(ProcessInstance.process_id == process_id,
                                                              ProcessInstance.do_evaluate.is_(True))). \
        order_by(asc(ProcessInstance.instantiation_time))
    requests_a = []
    requests_b = []
    requests_a_counter = 0
    requests_b_counter = 0
    for instance in all_instances_ordered:
        if instance.decision == Version.A:
            requests_a_counter += 1
        elif instance.decision == Version.B:
            requests_b_counter += 1
        else:
            abort(500, ("Unexpected decision for instance " + str(instance.id) + " " + str(instance.decision)))

        requests_a.append(requests_a_counter)
        requests_b.append(requests_b_counter)

    return {
        "noTotalRequests": all_instances_ordered.count(),
        "requestsA": requests_a,
        "requestsB": requests_b
    }


@instance_router_api.route('/aggregate-data/client-requests/outside-batch', methods=['GET'])
# pylint: disable=missing-return-doc, missing-return-type-doc
def get_instantiation_data_outside_batch():
    """ Get number of client requests that have been routed outside of batches for a certain process """
    process_id = int(request.args.get('process-id'))
    validate_backend_process_id(process_id)
    return {
        "numberOfRequests": ProcessInstance.query.filter(and_(ProcessInstance.process_id == process_id,
                                                              ProcessInstance.do_evaluate.is_(False))).count()
    }


@instance_router_api.route('/aggregate-data/evaluation-progress', methods=['GET'])
# pylint: disable=missing-return-doc, missing-return-type-doc
def get_evaluation_progress():
    """ Get info on evaluation progress """
    process_id = int(request.args.get('process-id'))
    validate_backend_process_id(process_id)
    total_to_be_evaluated_count = ProcessInstance.query.filter(and_(ProcessInstance.do_evaluate.is_(True),
                                                                    ProcessInstance.process_id == process_id)).count()
    already_evaluated_count = ProcessInstance.query.filter(and_(ProcessInstance.do_evaluate.is_(True),
                                                                      ProcessInstance.process_id == process_id,
                                                                      ProcessInstance.finished_time.is_not(None),
                                                                      ProcessInstance.reward.is_not(None))).count()
    not_yet_evaluated_count = ProcessInstance.query.filter(and_(ProcessInstance.do_evaluate.is_(True),
                                                                      ProcessInstance.process_id == process_id,
                                                                      ProcessInstance.finished_time.is_(None),
                                                                      ProcessInstance.reward.is_(None))).count()
    assert not_yet_evaluated_count + already_evaluated_count == total_to_be_evaluated_count
    return {
        "totalToBeEvaluatedCount": total_to_be_evaluated_count,
        "alreadyEvaluatedCount": already_evaluated_count,
        "notYetEvaluatedCount": not_yet_evaluated_count,
        "alreadyEvaluatedPerc":
            None if total_to_be_evaluated_count == 0 else already_evaluated_count / total_to_be_evaluated_count,
        "notYetEvaluatedPerc":
            None if total_to_be_evaluated_count == 0 else not_yet_evaluated_count / total_to_be_evaluated_count
    }


@instance_router_api.route('/detailed-data/batch', methods=['GET'])
# pylint: disable=missing-return-doc, missing-return-type-doc
def get_instances_batch():
    """ Get detailed data about every instance that has been routed for a certain process and batch """
    process_id = int(request.args.get('process-id'))
    validate_backend_process_id(process_id)
    batch_number = int(request.args.get('batch-number'))
    assert batch_number <= BatchPolicy.query.filter(BatchPolicy.process_id == process_id).count(), \
        "Batch number too high"
    data = {
        "processId": process_id,
        "batchNumber": batch_number,
        "instances": []
    }
    relevant_bapol_id = BatchPolicy.query.filter(BatchPolicy.process_id == process_id) \
        .order_by(asc(BatchPolicy.id))[batch_number - 1].id
    relevant_instances = ProcessInstance.query.filter(ProcessInstance.batch_policy_id == relevant_bapol_id) \
        .order_by(asc(ProcessInstance.id))
    for instance in relevant_instances:
        data.get('instances').append({
            "decision": instance.decision.value,
            "customerCategory": instance.customer_category,
            "startTime": instance.instantiation_time,
            "endTime": instance.finished_time,
            "reward": instance.reward,
            "rlProb": instance.rl_prob
        })
    return data


@instance_router_api.route('/finished-instance-count', methods=['GET'])
# pylint: disable=missing-return-doc, missing-return-type-doc
def count_finished_instances():
    """ Get number of finished instances for a certain process, both in and outside of batches """
    process_id = int(request.args.get('process-id'))
    validate_backend_process_id(process_id)
    count = ProcessInstance.query.filter(and_(ProcessInstance.finished_time.is_not(None),
                                              ProcessInstance.process_id == process_id)).count()

    return {
        'finishedInstanceCount': count
    }
