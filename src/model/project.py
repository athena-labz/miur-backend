import uuid

from . import db

from model.judge_project_association import association_table
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey


def str_uuid():
    return str(uuid.uuid4())


class Project(db.Model):
    __tablename__ = "project"

    id = db.Column(db.Integer, primary_key=True)
    project_identifier = db.Column(
        db.String(64), default=str_uuid, nullable=False)

    proposer_id = db.Column(db.Integer, ForeignKey(
        "user.id"), nullable=False)
    proposer = relationship("User", back_populates="created_projects")
    
    name = db.Column(db.String(), nullable=False)

    short_description = db.Column(db.String(), nullable=False)
    long_description = db.Column(db.String(), nullable=False)

    funding_currency = db.Column(db.String(64), nullable=False)
    funding_achieved = db.Column(db.Integer, default=0, nullable=False)
    funding_expected = db.Column(db.Integer, nullable=False)

    deliverables = relationship("Deliverable", back_populates="project")
    judges = relationship(
        "Judge", secondary=association_table, back_populates="projects")

    project_funding = relationship("Fund", back_populates="project")

    project_state = relationship(
        "ProjectState", back_populates="project", uselist=False)
