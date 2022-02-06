from flask import Blueprint, abort, request, jsonify

from rest import utils
from models import db
from models.batch_policy import BatchPolicy, ExecutionStrategyBaPol, get_current_bapol_data
from models.process import Process, is_valid_customer_category
from models.batch_policy_proposal import exists_bapol_proposal_without_bapol, get_current_open_proposal

batch_policy_api = Blueprint('batch_policy_api', __name__)


# TODO: add sanity checks of data (percentages add up e.g.)
@batch_policy_api.route('', methods=['POST'])
def set_batch_policy():
    """ Set new batch policy for currently active process

     An open proposal has to be available to do this.
     """
    process_id = int(request.args.get('process-id'))
    utils.validate_backend_process_id(process_id)
    if not exists_bapol_proposal_without_bapol(process_id):
        abort(404, "No prior open batch policy proposal for this process found.")

    json = request.json
    assert 'batchSize' in json.keys()
    assert 'executionStrategy' in json.keys()
    if 'batchSize' not in json.keys() \
            or 'executionStrategy' not in json.keys():
        abort(400, "Wrong JSON format")
    batch_size = json.get('batchSize')
    execution_strategies_json = json.get('executionStrategy')
    execution_strategies_table_rows = []
    for elem in execution_strategies_json:
        if 'explorationProbabilityA' not in elem.keys() \
                or 'explorationProbabilityB' not in elem.keys() \
                or 'customerCategory' not in elem.keys():
            abort(400, "Wrong JSON format")
        if not is_valid_customer_category(process_id, elem.get('customerCategory')):
            abort(400, "Not a valid customer category")
        execution_strategies_table_rows.append(ExecutionStrategyBaPol(
            customer_category=elem.get('customerCategory'),
            exploration_probability_a=elem.get('explorationProbabilityA'),
            exploration_probability_b=elem.get('explorationProbabilityB')
        ))
    relevant_process_query = db.session.query(Process).filter(Process.id == process_id)
    assert relevant_process_query.count() == 1, "Amount of active processes in db != 1"
    relevant_process = relevant_process_query.first()
    batch_policy = BatchPolicy(batch_size=batch_size,
                               execution_strategies=execution_strategies_table_rows,
                               batch_policy_proposal=get_current_open_proposal(process_id))
    relevant_process.batch_policies.append(batch_policy)
    db.session.add(batch_policy)
    for elem in execution_strategies_table_rows:
        db.session.add(elem)
    db.session.commit()

    # Assumption: when we reach this point, it was successful
    return "Success"


@batch_policy_api.route('/latest', methods=['GET'])
def get_batch_policy():
    """ Get latest batch policy of currently active process """
    active_pv_query = db.session.query(Process).filter(Process.active.is_(True))
    active_pv = None
    if active_pv_query.count() == 0:
        abort(404, "No currently active process.")
    elif active_pv_query.count() > 1:
        abort(500, "Internal server error: More than one active process")
    elif active_pv_query.count() == 1:
        active_pv = active_pv_query.first()
    data_dict = get_current_bapol_data(active_pv.id)
    return data_dict


@batch_policy_api.route('/count', methods=['GET'])
def get_batch_policy_count():
    """ Get amount of batch policies that have been set / entries in batch_policy db table for a certain process """
    process_id = int(request.args.get('process-id'))
    utils.validate_backend_process_id(process_id)
    return {
        "processId": process_id,
        "batchPolicyCount": BatchPolicy.query.filter(BatchPolicy.process_id == process_id).count()
    }
