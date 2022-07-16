import uuid

from . import db

from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, func


def str_uuid():
    return str(uuid.uuid4())


class Deliverable(db.Model):
    __tablename__ = "deliverable"

    id = db.Column(db.Integer, primary_key=True)
    deliverable_identifier = db.Column(
        db.String(64), default=str_uuid, nullable=False)
    deliverable_index = db.Column(db.Integer, nullable=False)

    project_id = db.Column(db.Integer, ForeignKey(
        "project.id"), nullable=False)
    project = relationship("Project", back_populates="deliverables")

    declaration = db.Column(db.String(), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    percentage_requested = db.Column(db.Integer, nullable=False)
