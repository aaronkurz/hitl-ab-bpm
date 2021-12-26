from datetime import datetime
from models import db


class ProcessVariants(db.Model):
    __tablename__ = "process_variants"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    datetime_added = db.Column(db.DateTime, nullable=False, default=datetime.now())
    variant_a = db.Column(db.String, nullable=False)
    variant_b = db.Column(db.String, nullable=False)
