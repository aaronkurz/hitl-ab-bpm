from datetime import datetime
from models import db
from models.process_instance import ProcessInstance
from models.batch_policy import BatchPolicy
from sqlalchemy.orm import relationship
from models.utils import CASCADING_DELETE, Version, WinningReasonEnum


class Process(db.Model):
    __tablename__ = "process"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    datetime_added = db.Column(db.DateTime, nullable=False, default=datetime.now())
    customer_categories = db.Column(db.String, nullable=False)
    variant_a_path = db.Column(db.String, nullable=False)
    variant_b_path = db.Column(db.String, nullable=False)
    variant_a_camunda_id = db.Column(db.String, nullable=False)
    variant_b_camunda_id = db.Column(db.String, nullable=False)
    default_version = db.Column(db.Enum(Version), nullable=False)
    a_hist_min_duration = db.Column(db.Float, nullable=False)
    a_hist_max_duration = db.Column(db.Float, nullable=False)
    winning_version = db.Column(db.Enum(Version), nullable=True)  # Will be set after learning is done
    winning_reason = db.Column(db.Enum(WinningReasonEnum), nullable=True)
    datetime_decided = db.Column(db.DateTime, nullable=True)
    batch_policies = relationship("BatchPolicy", cascade=CASCADING_DELETE)
    process_instances = relationship("ProcessInstance", cascade=CASCADING_DELETE)
    batch_policy_proposals = relationship('BatchPolicyProposal', cascade=CASCADING_DELETE)


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
        'default_version':  None if relevant_process_entry.default_version is None else relevant_process_entry.default_version.value,
        'winning_version': None if relevant_process_entry.winning_version is None else relevant_process_entry.winning_version.value,
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
        raise RuntimeError("version-decision query parameter must be 'a' or 'b'")
    relevant_process = Process.query.filter(Process.id == process_id).first()
    if relevant_process.winning_version is not None:
        raise RuntimeError("This process already has a winning version")
    relevant_process.winning_version = decision
    relevant_process.winning_reason = WinningReasonEnum.manualChoice
    relevant_process.datetime_decided = datetime.now()
    db.session.commit()
    return get_process_metadata(process_id)


def is_valid_customer_category(process_id: int, customer_category: str):
    process = Process.query.filter(Process.id == process_id).first()
    customer_categories_list = process.customer_categories.split("-")
    if customer_category in customer_categories_list:
        return True
    else:
        return False

