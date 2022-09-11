import uuid

from . import db

from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, func

from model.project_subject_association import association_table
from model.project_mediator_association import association_table as mediator_association_table


class Project(db.Model):
    __tablename__ = "project"

    id = db.Column(db.Integer, primary_key=True)
    project_identifier = db.Column(
        db.String(64), default=lambda: str(uuid.uuid4()), nullable=False)

    creator_id = db.Column(db.Integer, ForeignKey("user.id"), nullable=False)
    creator = relationship("User", back_populates="created_projects")

    subjects = relationship(
        "Subject", secondary=association_table, back_populates="projects")

    name = db.Column(db.String(), nullable=False)

    short_description = db.Column(db.String(), nullable=False)
    long_description = db.Column(db.String(), nullable=False)

    reward_requested = db.Column(db.Integer, nullable=False)
    days_to_complete = db.Column(db.Integer, nullable=False)
    collateral = db.Column(db.Integer, nullable=False)

    deliverables = relationship("Deliverable", back_populates="project")
    mediators = relationship(
        "User", secondary=mediator_association_table, back_populates="mediated_projects")

    start_date = db.Column(db.DateTime(timezone=False), nullable=False)

    creation_date = db.Column(db.DateTime(
        timezone=False), server_default=func.now(), nullable=False)
