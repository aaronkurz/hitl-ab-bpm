from datetime import datetime
from models import db
from models.process_instance import ProcessInstance
from models.batch_policy import BatchPolicy
from sqlalchemy.orm import relationship
import enum


class WinningReasonEnum(enum.Enum):
    experimentEnded = "Experiment ended"
    manualChoice = "Manual choice by human expert"


class Version(enum.Enum):
    a = 'a'
    b = 'b'


class Process(db.Model):
    __tablename__ = "process"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    datetime_added = db.Column(db.DateTime, nullable=False, default=datetime.now())
    variant_a_path = db.Column(db.String, nullable=False)
    variant_b_path = db.Column(db.String, nullable=False)
    variant_a_camunda_id = db.Column(db.String, nullable=False)
    variant_b_camunda_id = db.Column(db.String, nullable=False)
    winning_version = db.Column(db.Enum(Version), nullable=True)  # Will be set after learning is done
    winning_reason = db.Column(db.Enum(WinningReasonEnum), nullable=True)
    datetime_decided = db.Column(db.DateTime, nullable=True)
    batch_policies = relationship("BatchPolicy", cascade="all, delete")
    process_instances = relationship("ProcessInstance", cascade="all, delete")


def get_process_metadata(process_id: int) -> dict:
    """ Get data about specified process """
    relevant_process_entry_query = db.session.query(Process).filter(Process.id == process_id)
    assert relevant_process_entry_query.count() == 1, "Active processes != 1: " + \
                                                      str(relevant_process_entry_query.count())
    relevant_process_entry = relevant_process_entry_query.first()
    ap_info = {
        'id': relevant_process_entry.id,
        'name': relevant_process_entry.name,
        'variant_a_path': relevant_process_entry.variant_a_path,
        'variant_b_path': relevant_process_entry.variant_b_path,
        'variant_a_camunda_id': relevant_process_entry.variant_a_camunda_id,
        'variant_b_camunda_id': relevant_process_entry.variant_b_camunda_id,
        'winning_version': relevant_process_entry.winning_version,
        'winning_reason': relevant_process_entry.winning_reason,
        'datetime_decided': relevant_process_entry.datetime_decided,
        'number_batch_policies':
            BatchPolicy.query.filter(BatchPolicy.process_id == relevant_process_entry.id).count(),
        'number_instances':
            ProcessInstance.query.filter(ProcessInstance.process_id == relevant_process_entry.id).count()
    }
    return ap_info


def get_active_process_metadata() -> dict:
    """ Get data about currently active process """
    active_process_entry_query = db.session.query(Process).filter(Process.active.is_(True))
    assert active_process_entry_query.count() == 1, "Active processes != 1: " + str(active_process_entry_query.count())
    active_process_entry_id = active_process_entry_query.first().id
    return get_process_metadata(active_process_entry_id)


def set_winning(process_id: int, decision: str) -> dict:
    """ Finish an experiment and set a winning version for a process

     :param process_id: process id in backend
     :param decision: 'a' or 'b'
    """
    if decision not in ['a', 'b']:
        raise Exception("version-decision query parameter must be 'a' or 'b'")
    relevant_process = Process.query.filter(Process.id == process_id).first()
    if relevant_process.winning_version is not None:
        raise Exception("This process already has a winning version")
    relevant_process.winning_version = decision
    relevant_process.winning_reason = WinningReasonEnum.manualChoice
    relevant_process.datetime_decided = datetime.now()
    db.session.commit()
    return get_process_metadata(process_id)