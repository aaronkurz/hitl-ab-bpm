""" sqlalchemy model for processes and related functions.
A process row is a certain experiment with multiple versions of that process and further metadata.
"""
from datetime import datetime
from models import db
from models.process_instance import ProcessInstance, unevaluated_instances_still_exist
from models.batch_policy import BatchPolicy
from models.utils import CASCADING_DELETE, Version, WinningReasonEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY


class Process(db.Model):
    """ sqlalchemy model for processes/experiments """
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
    quantiles_default_history = db.Column(ARRAY(db.Float), nullable=False) # in seconds
    interarrival_default_history = db.Column(db.Float, nullable=False)
    in_cool_off = db.Column(db.Boolean, nullable=False, default=False)
    winning_version = db.Column(db.Enum(Version), nullable=True)  # Will be set after learning is done
    winning_reason = db.Column(db.Enum(WinningReasonEnum), nullable=True)
    datetime_decided = db.Column(db.DateTime, nullable=True)
    batch_policies = relationship("BatchPolicy", cascade=CASCADING_DELETE)
    process_instances = relationship("ProcessInstance", cascade=CASCADING_DELETE)
    batch_policy_proposals = relationship('BatchPolicyProposal', cascade=CASCADING_DELETE)


def get_process_metadata(process_id: int) -> dict:
    """Get data about specified process.

    :param process_id: specify process
    :return: metadata about process
    """
    relevant_process_entry_query = db.session.query(Process).filter(Process.id == process_id)
    assert relevant_process_entry_query.count() == 1, "Active processes != 1: " + \
                                                      str(relevant_process_entry_query.count())
    relevant_process_entry = relevant_process_entry_query.first()
    ap_info = {
        'id': relevant_process_entry.id,
        'name': relevant_process_entry.name,
        'customer_categories': relevant_process_entry.customer_categories,
        'variant_a_path': relevant_process_entry.variant_a_path,
        'variant_b_path': relevant_process_entry.variant_b_path,
        'variant_a_camunda_id': relevant_process_entry.variant_a_camunda_id,
        'variant_b_camunda_id': relevant_process_entry.variant_b_camunda_id,
        'default_version':
            None if relevant_process_entry.default_version is None else relevant_process_entry.default_version.value,
        'winning_version':
            None if relevant_process_entry.winning_version is None else relevant_process_entry.winning_version.value,
        'winning_reason': relevant_process_entry.winning_reason,
        'datetime_decided': relevant_process_entry.datetime_decided,
        'number_batch_policies':
            BatchPolicy.query.filter(BatchPolicy.process_id == relevant_process_entry.id).count(),
        'number_instances':
            ProcessInstance.query.filter(ProcessInstance.process_id == relevant_process_entry.id).count()
    }
    return ap_info


def get_active_process_metadata() -> dict:
    """Get data about currently active process.

    :return: data about active process
    """
    active_process_entry_query = db.session.query(Process).filter(Process.active.is_(True))
    assert active_process_entry_query.count() == 1, "Active processes != 1: " + str(active_process_entry_query.count())
    active_process_entry_id = active_process_entry_query.first().id
    return get_process_metadata(active_process_entry_id)


def set_winning(process_id: int, decision: Version, winning_reason: WinningReasonEnum) -> dict:
    """ Finish an experiment and set a winning version for a process, as well as a winning reason

    :raises RuntimeError: process already has winning version
    :raises RuntimeError: version-decision query parameter must be 'a' or 'b'
    :param winning_reason:
    :param process_id: process id in backend
    :param decision: Version.A or Version.B
    :return: process metadata
    """
    if decision not in [Version.A, Version.B]:
        raise RuntimeError("version-decision query parameter must be Version.A or Version.B")
    relevant_process = Process.query.filter(Process.id == process_id).first()
    if relevant_process.winning_version is not None:
        raise RuntimeError("This process already has a winning version")
    relevant_process.winning_version = decision
    relevant_process.winning_reason = winning_reason
    relevant_process.datetime_decided = datetime.now()
    db.session.commit()
    return get_process_metadata(process_id)


def is_valid_customer_category(process_id: int, customer_category: str) -> bool:
    """Checks whether a customer_category string is part of the customer categories of a certain process.

    :param process_id: process to be checked
    :param customer_category: category to be checked
    :return: True or False
    """
    process = Process.query.filter(Process.id == process_id).first()
    customer_categories_list = process.customer_categories.split("-")
    return customer_category in customer_categories_list


def in_cool_off(process_id: int) -> bool:
    """Checks whether a certain process is in cool-off period.

    :param process_id: specify process
    :return: True or False
    """
    return Process.query.filter(Process.id == process_id).first().in_cool_off


def cool_off_over(process_id: int) -> bool:
    """Checks whether a certain process is in cool-off period AND all  instances have been evaluated.

    :param process_id: specify process
    :return: True or False
    """
    return in_cool_off(process_id) and not unevaluated_instances_still_exist(process_id)
