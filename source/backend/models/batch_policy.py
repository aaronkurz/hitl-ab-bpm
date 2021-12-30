from models import db
from models.processes import ProcessVariants


class BatchPolicy(db.Model):
    __tablename__ = 'batch_policy'
    id = db.Column(db.Integer, primary_key=True)
    batch_size = db.Column(db.Integer, nullable=False)
    process_id = db.Column(db.Integer, db.ForeignKey('process_variant.id'))
    last_modified = db.Column(db.DateTime, nullable=False)
    execution_strategies = db.relationship('ExecutionStrategyBaPol', backref='batch_policy', cascade="all, delete")


class ExecutionStrategyBaPol(db.Model):
    __tablename__ = "execution_strategy_bapol"
    batch_policy_id = db.Column(db.Integer, db.ForeignKey('batch_policy.id'), primary_key=True)
    customer_category = db.Column(db.String(100), primary_key=True)
    exploration_probability_a = db.Column(db.Float, default=0.5, nullable=False)
    exploration_probability_b = db.Column(db.Float, default=0.5, nullable=False)


def get_current_bapol(process_id: int) -> dict:
    """ Get the latest (= currently active) bapol of specified process """
    latest_bapol = BatchPolicy.query.order_by(BatchPolicy.last_modified.desc())\
        .filter(BatchPolicy.process_id == process_id).first()
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
    return data


def get_current_bapol_active_process():
    """ Get the latest (= currently active) bapol of specified process """
    active_pv_query = db.session.query(ProcessVariants).filter(ProcessVariants.active.is_(True))
    active_pv = None
    if active_pv_query.count() == 0:
        raise Exception("No currently active process.")
    elif active_pv_query.count() > 1:
        raise Exception("More than one active process")
    elif active_pv_query.count() == 1:
        active_pv = active_pv_query.first()
    return get_current_bapol(active_pv.id)
