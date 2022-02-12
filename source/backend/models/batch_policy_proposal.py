from datetime import datetime
from sqlalchemy import and_

from models import db
from models.process import Process


class BatchPolicyProposal(db.Model):
    __tablename__ = 'batch_policy_proposal'
    id = db.Column(db.Integer, primary_key=True)
    process_id = db.Column(db.Integer, db.ForeignKey('process.id'))
    time_added = db.Column(db.DateTime, nullable=False, default=datetime.now())
    execution_strategies = db.relationship('ExecutionStrategyBaPolProp',
                                           backref='batch_policy_proposal',
                                           cascade="all, delete")
    batch_policy_id = db.Column(db.Integer, db.ForeignKey('batch_policy.id'))


class ExecutionStrategyBaPolProp(db.Model):
    __tablename__ = "execution_strategy_bapol_prop"
    batch_policy_id = db.Column(db.Integer, db.ForeignKey('batch_policy_proposal.id'), primary_key=True)
    customer_category = db.Column(db.String(100), primary_key=True)
    exploration_probability_a = db.Column(db.Float, nullable=False)
    exploration_probability_b = db.Column(db.Float, nullable=False)


def set_naive_bapol_proposal(process_id: int, customer_categories: [str]):
    expl_probs_a = []
    expl_probs_b = []
    for _ in customer_categories:
        expl_probs_a.append(0.5)
        expl_probs_b.append(0.5)
    set_bapol_proposal(process_id, customer_categories, expl_probs_a, expl_probs_b)


def set_bapol_proposal(process_id: int, customer_categories: [str], expl_probs_a: [float], expl_probs_b: [float]) -> bool:
    assert _new_proposal_can_be_set(process_id)
    assert len(customer_categories) == len(expl_probs_a) \
           and len(expl_probs_a) == len(expl_probs_b), "Length of input lists must be the same"
    exec_strat_props = []
    for i in range(len(customer_categories)):
        assert expl_probs_a[i] + expl_probs_b[i] == 1.0, "Probabilities do not add up to 1.0 for each category"
        exec_strat_props.append(
            ExecutionStrategyBaPolProp(
                customer_category=customer_categories[i],
                exploration_probability_a=expl_probs_a[i],
                exploration_probability_b=expl_probs_b[i]
            )
        )
    new_proposal = BatchPolicyProposal(
        execution_strategies=exec_strat_props
    )
    process = Process.query.filter(Process.id == process_id).first()
    process.batch_policy_proposals.append(new_proposal)
    db.session.commit()
    return True


def _new_proposal_can_be_set(process_id) -> bool:
    relevant_process = Process.query.filter(Process.id == process_id).first()
    if relevant_process.winning_version is not None or exists_bapol_proposal_without_bapol(process_id):
        return False
    else:
        return True


def exists_bapol_proposal_without_bapol(process_id) -> bool:
    if Process.query.filter(Process.id == process_id).first().winning_version != None:
        return False
    count_props_without_bapol = BatchPolicyProposal.query. \
        filter(and_(BatchPolicyProposal.process_id == process_id,
                    BatchPolicyProposal.batch_policy_id == None)).count()
    if count_props_without_bapol == 0:
        return False
    elif count_props_without_bapol == 1:
        return True
    else:
        raise RuntimeError("Illegal state: More than one batch policy proposal without corresponding batch policy")


def get_current_open_proposal_data(process_id: int) -> dict:
    if not exists_bapol_proposal_without_bapol(process_id):
        raise RuntimeError("No open batch policy proposal")

    relevant_bapol_prop = get_current_open_proposal(process_id)
    exec_strats = []
    for exec_strat in relevant_bapol_prop.execution_strategies:
        exec_strats.append(dict(customerCategory=exec_strat.customer_category,
                                explorationProbabilityA=exec_strat.exploration_probability_a,
                                explorationProbabilityB=exec_strat.exploration_probability_b))

    return {
            'processId': process_id,
            'baPolId': relevant_bapol_prop.batch_policy_id,
            'executionStrategy': exec_strats
        }


def get_current_open_proposal(process_id: int) -> BatchPolicyProposal:
    if not exists_bapol_proposal_without_bapol(process_id):
        raise RuntimeError("No open batch policy proposal")

    relevant_bapol_prop = BatchPolicyProposal.query.filter(and_(BatchPolicyProposal.process_id == process_id,
                                                                BatchPolicyProposal.batch_policy_id == None)).first()

    return relevant_bapol_prop
