""" sqlalchemy model for processes and related functions.
A process row is a certain experiment with multiple versions of that process and further metadata.
"""
from datetime import datetime
from typing import Optional

from models import db
from models.process_instance import unevaluated_instances_still_exist
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
    variant_a_path = db.Column(db.String, nullable=False)
    variant_b_path = db.Column(db.String, nullable=False)
    variant_a_camunda_id = db.Column(db.String, nullable=False)
    variant_b_camunda_id = db.Column(db.String, nullable=False)
    default_version = db.Column(db.Enum(Version), nullable=False)
    quantiles_default_history = db.Column(ARRAY(db.Float), nullable=False) # in seconds
    interarrival_default_history = db.Column(db.Float, nullable=False)
    in_cool_off = db.Column(db.Boolean, nullable=False, default=False)
    winning_reason = db.Column(db.Enum(WinningReasonEnum), nullable=True)
    datetime_decided = db.Column(db.DateTime, nullable=True)
    batch_policies = relationship("BatchPolicy", cascade=CASCADING_DELETE)
    customer_categories = relationship("CustomerCategory", cascade=CASCADING_DELETE, lazy="dynamic")
    process_instances = relationship("ProcessInstance", cascade=CASCADING_DELETE)
    batch_policy_proposals = relationship('BatchPolicyProposal', cascade=CASCADING_DELETE)


class CustomerCategory(db.Model):
    """ sqlalchemy model for customer categories of a process """
    __tablename__ = "customer_category"
    id = db.Column(db.Integer, primary_key=True)
    process_id = db.Column(db.Integer, db.ForeignKey('process.id'))
    name = db.Column(db.String(100), nullable=False)
    winning_version = db.Column(db.Enum(Version), nullable=True)  # Will be set after learning is done


def get_active_process_id() -> int:
    """Get backend id of currently active process.

    :return: process id
    """
    active_process_entry_query = db.session.query(Process).filter(Process.active.is_(True))
    assert active_process_entry_query.count() == 1, "Active processes != 1: " + str(active_process_entry_query.count())
    active_process_entry_id = active_process_entry_query.first().id
    return active_process_entry_id


def get_process_entry(process_id: int) -> Process:
    """Get process entry

    :raises AssertionError: When illegal state: Active processes != 1
    :param process_id: specify process
    :return: Process entry
    """
    active_process_entry_query = db.session.query(Process).filter(Process.id == process_id)
    assert active_process_entry_query.count() == 1, "Active processes != 1: " + str(active_process_entry_query.count())
    return active_process_entry_query.first()


def set_winning(process_id: int, decision: list[dict[str, Version]], winning_reason: WinningReasonEnum) -> None:
    """ Finish an experiment and set the winning versions/decision for a process, as well as a winning reason

    :raises RuntimeError: process already has winning version
    :raises RuntimeError: version-decision query parameter must be 'a' or 'b'
    :param process_id: process id in backend
    :param decision: A list containing dicts with the decisions for each customer category. Dict format:
    {'customer_category': str, 'winning_version': Version.A or Version.B}
    :param winning_reason: reason for decision
    """
    if is_decision_made(process_id):
        raise RuntimeError("Winning decision already set")

    relevant_process = get_process_entry(process_id)
    relevant_customer_categories = relevant_process.customer_categories

    # check whether handed over decision dict is valid
    if not relevant_customer_categories.count() == len(decision):
        raise RuntimeError("Decisions not provided for all customer categories")
    category_names = []
    for part_decision in decision:
        if part_decision['winning_version'] not in [Version.A, Version.B]:
            raise RuntimeError("winning_version must be Version.A or Version.B")
        category_names.append(part_decision['customer_category'])
    category_names.sort()
    if category_names != get_sorted_customer_category_list(process_id):
        raise RuntimeError("customer_category invalid for process")

    for part_decision in decision:
        # set winning version for customer category
        customer_category = relevant_customer_categories.\
            filter(CustomerCategory.name == part_decision['customer_category']).first()
        customer_category.winning_version = part_decision['winning_version']

    relevant_process.winning_reason = winning_reason
    relevant_process.datetime_decided = datetime.now()
    db.session.commit()


def is_valid_customer_category(process_id: int, customer_category: str) -> bool:
    """Checks whether a customer_category string is part of the customer categories of a certain process.

    :param process_id: process to be checked
    :param customer_category: category to be checked
    :return: True or False
    """
    relevant_process = get_process_entry(process_id)
    customer_categories = relevant_process.customer_categories
    return any(category.name == customer_category for category in customer_categories)


def get_sorted_customer_category_list(process_id: int) -> list:
    """Get a list of the customer categories of a process.

    :param process_id: specify process/experiment
    :return: sorted (alphabetically) list of customer categories
    """
    relevant_process = get_process_entry(process_id)
    customer_categories = relevant_process.customer_categories
    cat_names = []
    for category in customer_categories:
        cat_names.append(category.name)
    cat_names.sort()
    return cat_names


def is_decision_made(process_id: int) -> bool:
    """Check whether a decision has already been made for a certain process

    :raises RuntimeError: Illegal internal state: When only some of the customer categories have winning versions
    :param process_id: specify process
    :return: True or False
    """
    relevant_process = get_process_entry(process_id)
    customer_categories = relevant_process.customer_categories
    if all(category.winning_version is None for category in customer_categories):
        return False
    if all(category.winning_version is not None for category in customer_categories):
        return True
    raise RuntimeError("Either all, or none of the customer categories of a process should have a winning version")


def get_winning(process_id: int) -> Optional[list[Version]]:
    """Get a dict of the winning process versions per customer category.

    Format of dict:
    [{
        'customer_category': str,
        'winning_version': Version.A or Version.B
    }]
    :param process_id: specify process
    :return: list with winning version for each customer category or None, when no winning version yet
    """
    if not is_decision_made(process_id):
        winning_versions = None
    else:
        relevant_process_entry = get_process_entry(process_id)
        winning_versions = []
        for customer_category in relevant_process_entry.customer_categories:
            winning_versions.append(dict(customer_category=customer_category.name,
                                         winning_version=customer_category.winning_version))
    return winning_versions


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


def get_experiment_state(process_id: int) -> str:
    """Get the current state of the experiment for a certain process.

    :raises RuntimeError: Illegal internal state: Decision made without winning reason
    :param process_id: Process id
    :return: State of process experiment
    """
    process = get_process_entry(process_id)
    if is_decision_made(process_id) is False:
        if cool_off_over(process.id):
            return 'Cool-Off over, waiting for final decision'
        if process.in_cool_off:
            return 'In Cool-Off'
        return 'Running'
    if process.winning_reason is None:
        raise RuntimeError("Decision made without winning reason.")
    return "Done, " + process.winning_reason.value
