from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, func

from . import db


class ProjectState(db.Model):
    __tablename__ = "project_state"

    id = db.Column(db.Integer, primary_key=True)

    project_id = db.Column(db.Integer, ForeignKey(
        "project.id"), nullable=False)
    project = relationship("Project", back_populates="project_state")

    # draft, funding, progress, completed
    state = db.Column(db.String(16), nullable=False)

    tx_hash = db.Column(db.String(64))
    
    creation_date = db.Column(db.DateTime(
        timezone=False), server_default=func.now(), nullable=False)