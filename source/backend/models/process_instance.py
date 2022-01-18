from datetime import datetime
from models import db


class ProcessInstance(db.Model):
    __tablename__ = "process_instance"
    id = db.Column(db.Integer, primary_key=True)
    process_id = db.Column(db.Integer, db.ForeignKey('process_variant.id'))
    decision = db.Column(db.String, nullable=False)
    instantiation_time = db.Column(db.DateTime, nullable=False, default=datetime.now())
    camunda_instance_id = db.Column(db.String, nullable=False)
    # ^ these are set by the instantiating end-point after the request from a client
    # v these are set by the RL env after an instance is terminated
    finished_time = db.Column(db.DateTime, nullable=True)
    reward = db.Column(db.Float, nullable=True)

class TimeBasedCost(db.Model):
    __tablename__ = "time_based_cost"
    id = db.Column(db.Integer, primary_key=True)
    schedule_tbc = db.Column(db.Float, default=0, nullable=False)
    elegibility_test_tbc = db.Column(db.Float, default=0, nullable=False)
    medical_test_tbc = db.Column(db.Float, default=0, nullable=False)
    theory_test_tbc = db.Column(db.Float, default=0, nullable=False)
    practical_test_tbc = db.Column(db.Float, default=0, nullable=False)
    approve_tbc = db.Column(db.Float, default=0, nullable=False)
    reject_tbc = db.Column(db.Float, default=0, nullable=False)

class ActionProbability(db.Model):
    __tablename__ = "action_prob"
    id = db.Column(db.Integer, primary_key=True)
    variant_a_prob = db.Column(db.Float, default=0, nullable=False)
    variant_b_prob = db.Column(db.Float, default=0, nullable=False)

class RewardOverIteration(db.Model):
    __tablename__ = "reward_over_iteration"
    iteration_id = db.Column(db.Integer, primary_key=True)
    reward = db.Column(db.Float, default=0, nullable=False)