""" sqlalchemy models to store info about instantiated process instances and related functions """
from datetime import datetime
from sqlalchemy import and_
from models import db
from models.utils import Version


class ProcessInstance(db.Model):
    """ model to create table for process instances """
    __tablename__ = "process_instance"
    id = db.Column(db.Integer, primary_key=True)
    process_id = db.Column(db.Integer, db.ForeignKey('process.id'))
    batch_policy_id = db.Column(db.Integer, db.ForeignKey('batch_policy.id'))
    customer_category = db.Column(db.String, nullable=False)
    decision = db.Column(db.Enum(Version), nullable=False)
    do_evaluate = db.Column(db.Boolean, nullable=False)
    instantiation_time = db.Column(db.DateTime, nullable=False, default=datetime.now())
    camunda_instance_id = db.Column(db.String, nullable=False)
    # ^ these are set by the instantiating end-point after the request from a client
    # v these are set by the camunda_collector after an instance is terminated
    finished_time = db.Column(db.DateTime, nullable=True)  # if null, instance has not been determined as finished yet
    reward = db.Column(db.Float, nullable=True)  # if null, instance has not been taken into account for learning yet
    rl_prob = db.Column(db.Float, nullable=True)  # Probability with which the agent would have chosen the action...
    # ... (decision) given customer_category


def unevaluated_instances_still_exist(process_id: int) -> bool:
    """Checks whether unevaluated instances still exist for a given process id.

    :param process_id: process id
    :return: True or False
    """
    return ProcessInstance.query.filter(and_(ProcessInstance.process_id == process_id,
                                             ProcessInstance.do_evaluate.is_(True),
                                             ProcessInstance.reward.is_(None))).count() > 0
