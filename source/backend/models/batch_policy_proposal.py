from datetime import datetime
from sqlalchemy import and_

from models import db


class BatchPolicyProposal(db.Model):
    __tablename__ = 'batch_policy_proposal'
    id = db.Column(db.Integer, primary_key=True)
    process_id = db.Column(db.Integer, db.ForeignKey('process.id'))
    time_added = db.Column(db.DateTime, nullable=False, default=datetime.now())
    execution_strategies = db.relationship('ExecutionStrategyBaPolProp',
                                           backref='batch_policy_proposal',
                                           cascade="all, delete",
                                           nullable=False)
    batch_policy_id = db.Column(db.Integer, db.ForeignKey('batch_policy.id'))


class ExecutionStrategyBaPolProp(db.Model):
    __tablename__ = "execution_strategy_bapol_prop"
    batch_policy_id = db.Column(db.Integer, db.ForeignKey('batch_policy_proposal.id'), primary_key=True)
    customer_category = db.Column(db.String(100), primary_key=True)
    exploration_probability_a = db.Column(db.Float, nullable=False)
    exploration_probability_b = db.Column(db.Float, nullable=False)


def create_naive_bapol_proposal(customer_categories):
    """ Still has to be added to a process and added and committed to the db """
    exec_strat_props = []
    for category in customer_categories:
        exec_strat_props.append(
            ExecutionStrategyBaPolProp(
                customer_category=category,
                exploration_probability_a=0.5,
                exploration_probability_b=0.5
            )
        )
    new_proposal = BatchPolicyProposal(
        execution_strategies=exec_strat_props
    )
    return new_proposal


def exists_bapol_proposal_without_bapol(process_id) -> bool:
    count_props_without_bapol = BatchPolicyProposal.query. \
                                    filter(and_(BatchPolicyProposal.process_id == process_id,
                                                BatchPolicyProposal.batch_policy_id is None)).count()
    if count_props_without_bapol == 0:
        return False
    elif count_props_without_bapol == 1:
        return True
    else:
        raise RuntimeError("Illegal state: More than one batch policy proposal without corresponding batch policy")


def get_current_open_proposal(process_id: int) -> dict:
    if not exists_bapol_proposal_without_bapol(process_id):
        raise RuntimeError("No open batch policy proposal")

    relevant_bapol_prop = BatchPolicyProposal.query.filter(and_(BatchPolicyProposal.process_id == process_id,
                                          BatchPolicyProposal.batch_policy_id is None))
    exec_strats = []
    for exec_strat in relevant_bapol_prop:
        exec_strats.append(dict(customerCategory=exec_strat.customer_category,
                                explorationProbabilityA=exec_strat.exploration_probability_a,
                                explorationProbabilityB=exec_strat.exploration_probability_b))
    return {
        'processId': process_id,
        'executionStrategies': exec_strats
    }

