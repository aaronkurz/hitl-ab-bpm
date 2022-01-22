from flask import Blueprint, abort
from models.batch_policy import BatchPolicy, ExecutionStrategyBaPol, get_current_bapol
from models.process import Process
from flask import request
from datetime import datetime
from models import db
from flask import jsonify

batch_policy_api = Blueprint('batch_policy_api', __name__)


# TODO: add sanity checks of data (percentages add up e.g.)
@batch_policy_api.route('', methods=['POST'])
def set_batch_policy():
    """ Set new batch policy for currently active process """
    json = request.json

    batch_size = json.get('batchSize')
    execution_strategies_json = json.get('executionStrategy')
    execution_strategies_table_rows = []
    for elem in execution_strategies_json:
        execution_strategies_table_rows.append(ExecutionStrategyBaPol(
            customer_category=elem.get('customerCategory'),
            exploration_probability_a=elem.get('explorationProbabilityA'),
            exploration_probability_b=elem.get('explorationProbabilityB')
        ))
    active_process_query = db.session.query(Process).filter(Process.active.is_(True))
    assert active_process_query.count() == 1, "Amount of active processes in db != 1"
    active_process = active_process_query.first()
    batch_policy = BatchPolicy(batch_size=batch_size,
                               process_id=active_process.id,
                               time_added=datetime.now(),
                               execution_strategies=execution_strategies_table_rows)

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
    data_dict = get_current_bapol(active_pv.id)
    return data_dict


@batch_policy_api.route('/count', methods=['GET'])
def get_batch_policy_count():
    """ Get amount of batch policies that have been set / entries in batch_policy db table """
    data = {
        "batchPolicyCount": BatchPolicy.query.count()
    }
    json_data = jsonify(data)
    return json_data


@batch_policy_api.route('', methods=['DELETE'])
def delete_batch_policy_rows():
    db.session.query(ExecutionStrategyBaPol).delete()
    db.session.query(BatchPolicy).delete()
    db.session.commit()
    return "Success"
