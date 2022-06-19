""" SQLAlchemy models for batch policy proposal and related functions """
from datetime import datetime
from sqlalchemy import and_, desc
from models import db
from models.process import Process, cool_off_over, is_decision_made


class BatchPolicyProposal(db.Model):
    """ sqlalchemy model for batch policy proposal """
    __tablename__ = 'batch_policy_proposal'
    id = db.Column(db.Integer, primary_key=True)
    process_id = db.Column(db.Integer, db.ForeignKey('process.id'))
    time_added = db.Column(db.DateTime, nullable=False, default=datetime.now())
    final_proposal = db.Column(db.Boolean, nullable=False, default=False)
    execution_strategies = db.relationship('ExecutionStrategyBaPolProp',
                                           backref='batch_policy_proposal',
                                           cascade="all, delete")
    batch_policy_id = db.Column(db.Integer, db.ForeignKey('batch_policy.id'))


class ExecutionStrategyBaPolProp(db.Model):
    """ sqlalchemy model for execution strategies for batch policy proposals """
    __tablename__ = "execution_strategy_bapol_prop"
    batch_policy_proposal_id = db.Column(db.Integer, db.ForeignKey('batch_policy_proposal.id'), primary_key=True)
    customer_category = db.Column(db.String(100), primary_key=True)
    exploration_probability_a = db.Column(db.Float, nullable=False)
    exploration_probability_b = db.Column(db.Float, nullable=False)


def set_naive_bapol_proposal(process_id: int, customer_categories: list[str]):
    """Will set a naive (50:50) batch policy proposal for a certain process

    :param process_id: process id
    :param customer_categories: relevant customer categories for that process id
    """
    expl_probs_a = []
    expl_probs_b = []
    for _ in customer_categories:
        expl_probs_a.append(0.5)
        expl_probs_b.append(0.5)
    _set_bapol_proposal(process_id=process_id,
                        customer_categories=customer_categories,
                        expl_probs_a=expl_probs_a,
                        expl_probs_b=expl_probs_b,
                        final=False)


def _set_bapol_proposal(process_id: int,
                        customer_categories: list[str],
                        expl_probs_a: list[float],
                        expl_probs_b: list[float],
                        final: bool):
    """ Set a new batch policy proposal for a certain process.

    :param process_id: Specify for which process
    :param customer_categories: Customer categories
    :param expl_probs_a: Exploration strategy for a for each customer category (in same order)
    :param expl_probs_b: Exploration strategy for b for each customer category (in same order)
    :param final: Whether it is a final batch policy proposal
    """
    assert not is_decision_made(process_id)
    assert len(customer_categories) == len(expl_probs_a) \
           and len(expl_probs_a) == len(expl_probs_b), "Length of input lists must be the same"
    exec_strat_props = []
    for index, element in customer_categories:
        assert expl_probs_a[index] + expl_probs_b[
            index] == 1.0, "Probabilities do not add up to 1.0 for each category"
        exec_strat_props.append(
            ExecutionStrategyBaPolProp(
                customer_category=element,
                exploration_probability_a=expl_probs_a[index],
                exploration_probability_b=expl_probs_b[index]
            )
        )
    new_proposal = BatchPolicyProposal(
        execution_strategies=exec_strat_props
    )
    if final:
        new_proposal.final_proposal = True
    process = Process.query.filter(Process.id == process_id).first()
    process.batch_policy_proposals.append(new_proposal)
    db.session.commit()


def _update_bapol_proposal(proposal: BatchPolicyProposal, customer_categories: list[str],
                           expl_probs_a: list[float],
                           expl_probs_b: list[float],
                           final: bool):
    """ Update a certain batch policy proposal

    :raises RuntimeError: Problem with parameter customer_categories
    :param proposal: Proposal to be updated
    :param customer_categories: Customer categories
    :param expl_probs_a: Exploration strategy for a for each customer category (in same order)
    :param expl_probs_b: Exploration strategy for b for each customer category (in same order)
    :param final: Whether it is a final batch policy proposal
    """
    assert not is_decision_made(proposal.process_id)
    assert len(customer_categories) == len(expl_probs_a) \
           and len(expl_probs_a) == len(expl_probs_b), "Length of input lists must be the same"
    exec_strats = ExecutionStrategyBaPolProp.query \
        .filter(ExecutionStrategyBaPolProp.batch_policy_proposal_id == proposal.id)
    for exec_strat in exec_strats:
        try:
            relevant_index = customer_categories.index(exec_strat.customer_category)
        except ValueError as value_error:
            raise RuntimeError(
                "Missing customer category to update final batch policy proposal in cool off period"
            ) from value_error
        exec_strat.exploration_probability_a = expl_probs_a[relevant_index]
        exec_strat.exploration_probability_b = expl_probs_b[relevant_index]

    if final:
        proposal.final_proposal = True
    db.session.commit()


def set_or_update_bapol_proposal(process_id: int,
                                 customer_categories: list[str],
                                 expl_probs_a: list[float],
                                 expl_probs_b: list[float]):
    """Create a new batch policy proposal for a certain process, or if a currently open bapol proposal exists: update.

    :param process_id: process id in backend
    :param customer_categories: relevant customer categories of process
    :param expl_probs_a: exploration probabilities for a, the first one is for the first customer category and so on
    :param expl_probs_b: exploration probabilities for b, the first one is for the first customer category and so on
    """
    if not exists_bapol_proposal_without_bapol(process_id):
        # set a new batch policy proposal
        _set_bapol_proposal(process_id=process_id,
                            customer_categories=customer_categories,
                            expl_probs_a=expl_probs_a,
                            expl_probs_b=expl_probs_b,
                            final=False)
    else:
        # update latest batch policy proposal
        relevant_bapol_prop = BatchPolicyProposal.query.filter(BatchPolicyProposal.process_id == process_id) \
            .order_by(desc(BatchPolicyProposal.id)).first()
        _update_bapol_proposal(proposal=relevant_bapol_prop,
                               customer_categories=customer_categories,
                               expl_probs_a=expl_probs_a,
                               expl_probs_b=expl_probs_b,
                               final=False)


def set_or_update_final_bapol_proposal(process_id: int,
                                       customer_categories: list[str],
                                       expl_probs_a: list[float],
                                       expl_probs_b: list[float]):
    """Create a final batch policy proposal or update an existing final batch policy proposal for a given process id.

    In case there already is a final batch policy proposal, it is updated with the values passed to this function
    :raises RuntimeError: Unexpected number of final bapol proposals
    :param process_id: process id in our backend
    :param customer_categories: relevant customer categories of process
    :param expl_probs_a: exploration probabilities for a, the first one is for the first customer category and so on
    :param expl_probs_b: exploration probabilities for b, the first one is for the first customer category and so on
    """
    relevant_bapol_props = BatchPolicyProposal.query.filter(and_(BatchPolicyProposal.process_id == process_id,
                                                                 BatchPolicyProposal.final_proposal.is_(True)))
    if relevant_bapol_props.count() == 1:
        prop = relevant_bapol_props.first()
        _update_bapol_proposal(proposal=prop,
                               customer_categories=customer_categories,
                               expl_probs_a=expl_probs_a,
                               expl_probs_b=expl_probs_b,
                               final=True)
        return
    if relevant_bapol_props.count() == 0:
        _set_bapol_proposal(process_id=process_id,
                            customer_categories=customer_categories,
                            expl_probs_a=expl_probs_a,
                            expl_probs_b=expl_probs_b,
                            final=True)
        return
    raise RuntimeError("Unexpected number of final bapol proposals")


def exists_bapol_proposal_without_bapol(process_id: int) -> bool:
    """Checks whether there is a batch policy proposal without a corresponding batch policy

    Checks whether there is a batch policy proposal without a corresponding batch policy that has been set as a 'reply'
    for a certain process
    :raises RuntimeError: Illegal state: More than one batch policy proposal without corresponding batch policy
    :param process_id: process id in backend
    :return: True or False
    """
    if is_decision_made(process_id) is True \
            or Process.query.filter(Process.id == process_id).first().in_cool_off is True:
        return False
    count_props_without_bapol = BatchPolicyProposal.query. \
        filter(and_(BatchPolicyProposal.process_id == process_id,
                    BatchPolicyProposal.batch_policy_id.is_(None))).count()
    if count_props_without_bapol == 0:
        return False
    if count_props_without_bapol == 1:
        return True
    raise RuntimeError("Illegal state: More than one batch policy proposal without corresponding batch policy")


def get_current_open_proposal_data(process_id: int) -> dict:
    """Get data of currently open/unanswered (no corresponding batch policy yet) batch policy proposal

    Get data of currently open/unanswered (no corresponding batch policy yet) batch policy proposal for specified
    process id.
    :raises RuntimeError: There is no open batch policy proposal for specified process
    :param process_id: process id in backend
    :return: dict containing batch policy proposal
    """
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
    """Get BatchPolicyProposal for open proposal.

    :raises RuntimeError: No open batch policy proposal for process
    :param process_id: process id in backend
    :return:
    """
    if not exists_bapol_proposal_without_bapol(process_id):
        raise RuntimeError("No open batch policy proposal")

    relevant_bapol_prop = BatchPolicyProposal.query.filter(and_(BatchPolicyProposal.process_id == process_id,
                                                                BatchPolicyProposal.batch_policy_id.is_(None))).first()

    return relevant_bapol_prop


def get_final_proposal_data(process_id: int) -> dict:
    """Get data of final proposal.

    :raises RuntimeError: No final proposal available yet
    :param process_id: process id in backend
    :return: Final proposal
    """
    if not cool_off_over(process_id):
        raise RuntimeError("Final proposal not ready")
    relevant_bapol_prop_query = BatchPolicyProposal.query.filter(and_(BatchPolicyProposal.process_id == process_id,
                                                                      BatchPolicyProposal.final_proposal.is_(True)))
    assert relevant_bapol_prop_query.count() == 1

    relevant_bapol_prop = relevant_bapol_prop_query.first()

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
