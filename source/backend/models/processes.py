from datetime import datetime
from models import db
from sqlalchemy.orm import relationship


class ProcessVariants(db.Model):
    __tablename__ = "process_variant"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    datetime_added = db.Column(db.DateTime, nullable=False, default=datetime.now())
    variant_a_path = db.Column(db.String, nullable=False)
    variant_b_path = db.Column(db.String, nullable=False)
    variant_a_camunda_id = db.Column(db.String, nullable=False)
    variant_b_camunda_id = db.Column(db.String, nullable=False)
    batch_policies = relationship("BatchPolicy", cascade="all, delete")


def get_active_process():
    active_process_entry_query = db.session.query(ProcessVariants).filter(ProcessVariants.active.is_(True))
    assert active_process_entry_query.count() == 1, "Active processes != 1"
    active_process_entry = active_process_entry_query.first()
    ap_info = {
        'name': active_process_entry.name,
        'variant_a_path': active_process_entry.variant_a_path,
        'variant_b_path': active_process_entry.variant_b_path,
        'variant_a_camunda_id': active_process_entry.variant_a_camunda_id,
        'variant_b_camunda_id': active_process_entry.variant_b_camunda_id
    }
    return ap_info

