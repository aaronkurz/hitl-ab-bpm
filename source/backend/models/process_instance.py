from datetime import datetime
from models import db
from models.process import Version


class ProcessInstance(db.Model):
    __tablename__ = "process_instance"
    id = db.Column(db.Integer, primary_key=True)
    process_id = db.Column(db.Integer, db.ForeignKey('process.id'))
    batch_policy_id = db.Column(db.Integer, db.ForeignKey('batch_policy.id'))
    decision = db.Column(db.Enum(Version), nullable=False)
    do_evaluate = db.Column(db.Boolean, nullable=False)
    instantiation_time = db.Column(db.DateTime, nullable=False, default=datetime.now())
    camunda_instance_id = db.Column(db.String, nullable=False)
    # ^ these are set by the instantiating end-point after the request from a client
    # v these are set by the camunda_collector after an instance is terminated
    finished_time = db.Column(db.DateTime, nullable=True)  # if null, instance has not been determined as finished yet
    reward = db.Column(db.Float, nullable=True)  # if null, instance has not been taken into account for learning yet
