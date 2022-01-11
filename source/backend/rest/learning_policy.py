from flask import Blueprint, abort
from models.learning_policy import LearningPolicy, ExecutionStrategyLePol, get_current_lepol
from models.processes import ProcessVariants
from flask import request
from datetime import datetime
from models import db
from flask import jsonify

learning_policy_api = Blueprint('learning_policy_api', __name__)


# TODO: add sanity checks of data (percentages add up e.g.)
@learning_policy_api.route('', methods=['POST'])
def set_learning_policy():
    """ Set new learning policy for currently active process """
    json = request.json

    exp_length = json.get('experimentationLength')
    exp_decay = json.get('experimentationDecay')
    execution_strategies_json = json.get('executionStrategy')
    execution_strategies_table_rows = []
    for elem in execution_strategies_json:
        execution_strategies_table_rows.append(ExecutionStrategyLePol(
            customer_category=elem.get('customerCategory'),
            exploration_probability_a=elem.get('explorationProbabilityA'),
            exploration_probability_b=elem.get('explorationProbabilityB')
        ))
    active_process_query = db.session.query(ProcessVariants).filter(ProcessVariants.active.is_(True))
    assert active_process_query.count() == 1, "Amount of active processes in db != 1"
    active_process = active_process_query.first()
    learning_policy = LearningPolicy(exp_length=exp_length,
                                     exp_decay=exp_decay,
                                     process_id=active_process.id,
                                     last_modified=datetime.now(),
                                     execution_strategies=execution_strategies_table_rows)

    db.session.add(learning_policy)
    for elem in execution_strategies_table_rows:
        db.session.add(elem)
    db.session.commit()

    # Assumption: when we reach this point, it was successful
    return "Success"


@learning_policy_api.route('/latest', methods=['GET'])
def get_learning_policy():
    """ Get latest learning policy of currently active process """
    active_pv_query = db.session.query(ProcessVariants).filter(ProcessVariants.active.is_(True))
    active_pv = None
    if active_pv_query.count() == 0:
        abort(404, "No currently active process.")
    elif active_pv_query.count() > 1:
        abort(500, "Internal server error: More than one active process")
    elif active_pv_query.count() == 1:
        active_pv = active_pv_query.first()
    data_dict = get_current_lepol(active_pv.id)
    return data_dict


@learning_policy_api.route('/count', methods=['GET'])
def get_learning_policy_count():
    """ Get amount of learning policies that have been set / entries in learning_policy db table """
    data = {
        "learningPolicyCount": LearningPolicy.query.count()
    }
    json_data = jsonify(data)
    return json_data


@learning_policy_api.route('', methods=['DELETE'])
def delete_learning_policy_rows():
    db.session.query(ExecutionStrategyLePol).delete()
    db.session.query(LearningPolicy).delete()
    db.session.commit()
    return "Success"
