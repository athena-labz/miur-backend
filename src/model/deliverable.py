from . import db

from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey


class Deliverable(db.Model):
    __tablename__ = "deliverable"

    id = db.Column(db.Integer, primary_key=True)
    deliverable = db.Column(db.String(), nullable=False)

    project_id = db.Column(db.Integer, ForeignKey("project.id"), nullable=False)
    project = relationship("Project", back_populates="deliverables")
