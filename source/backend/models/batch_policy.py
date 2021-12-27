from models import db


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
