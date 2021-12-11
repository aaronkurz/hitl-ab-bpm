from flask import Blueprint
from models.batch_policy import BatchPolicy, ExecutionStrategyBaPol
from flask import request
from datetime import datetime
from models import db
from flask import jsonify

batch_policy_api = Blueprint('batch_policy_api', __name__)


@batch_policy_api.route('/', methods=['POST'])
def set_batch_policy():
    json = request.json

    batch_size = json.get('batchSize')
    process_definition_id_a = json.get('processDefinitionId_A')
    process_definition_id_b = json.get('processDefinitionId_B')
    execution_strategies_json = json.get('executionStrategy')
    execution_strategies_table_rows = []
    for elem in execution_strategies_json:
        execution_strategies_table_rows.append(ExecutionStrategyBaPol(
            customer_category=elem.get('customerCategory'),
            exploration_probability_a=elem.get('exploration_probability_A'),
            exploration_probability_b=elem.get('exploration_probability_B')
        ))
    batch_policy = BatchPolicy(batch_size=batch_size,
                               process_definition_id_a=process_definition_id_a,
                               process_definition_id_b=process_definition_id_b,
                               last_modified=datetime.now(),
                               execution_strategies=execution_strategies_table_rows)

    db.session.add(batch_policy)
    for elem in execution_strategies_table_rows:
        db.session.add(elem)
    db.session.commit()


@batch_policy_api.route('/count', methods=['GET'])
def get_batch_policy_count():
    data = {
        "batchPolicyCount": BatchPolicy.query.count()
    }
    json_data = jsonify(data)
    return json_data
