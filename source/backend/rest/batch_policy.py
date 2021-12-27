from flask import Blueprint
from models.batch_policy import BatchPolicy, ExecutionStrategyBaPol
from models.processes import ProcessVariants
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
    active_process_query = db.session.query(ProcessVariants).filter(ProcessVariants.active.is_(True))
    assert active_process_query.count() == 1, "Amount of active processes in db != 1"
    active_process = active_process_query.first()
    batch_policy = BatchPolicy(batch_size=batch_size,
                               process_id=active_process.id,
                               last_modified=datetime.now(),
                               execution_strategies=execution_strategies_table_rows)

    db.session.add(batch_policy)
    for elem in execution_strategies_table_rows:
        db.session.add(elem)
    db.session.commit()

    # Assumption: when we reach this point, it was successful
    return "Success"


@batch_policy_api.route('/latest', methods=['GET'])
def get_batch_policy():
    """ Get latest batch policy """
    latest_bapol: BatchPolicy = BatchPolicy.query.order_by(BatchPolicy.last_modified.desc()).first()
    exec_strats_rows: [ExecutionStrategyBaPol] = latest_bapol.execution_strategies
    exec_strats_dict = []
    for elem in exec_strats_rows:
        exec_strat = {
            "customerCategory": elem.customer_category,
            "explorationProbabilityA": elem.exploration_probability_a,
            "explorationProbabilityB": elem.exploration_probability_b
        }
        exec_strats_dict.append(exec_strat)
    data = {
        "lastModified": latest_bapol.last_modified,
        "batchSize": latest_bapol.batch_size,
        "processId": latest_bapol.process_id,
        "executionStrategy": exec_strats_dict
    }
    data_json = jsonify(data)
    return data_json


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
