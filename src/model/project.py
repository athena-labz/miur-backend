import uuid

from . import db

from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, func

from model.project_subject_association import (
    association_table as subjects_association_table,
)
from model.project_mediator_association import (
    association_table as mediator_association_table,
)


class Project(db.Model):
    __tablename__ = "project"

    id = db.Column(db.Integer, primary_key=True)
    project_identifier = db.Column(
        db.String(64), default=lambda: str(uuid.uuid4()), nullable=False
    )

    creator_id = db.Column(db.Integer, ForeignKey("user.id"), nullable=False)
    creator = relationship("User", back_populates="created_projects")

    subjects = relationship(
        "Subject", secondary=subjects_association_table, back_populates="projects"
    )

    name = db.Column(db.String(), nullable=False)

    short_description = db.Column(db.String(), nullable=False)
    long_description = db.Column(db.String(), nullable=False)

    days_to_complete = db.Column(db.Integer, nullable=False)

    deliverables = relationship("Deliverable", back_populates="project")
    mediators = relationship(
        "User", secondary=mediator_association_table, back_populates="mediated_projects"
    )
    funding = relationship("Funding", back_populates="project")
    submissions = relationship("Submission", back_populates="project")

    disqualified = db.Column(db.Boolean, default=False, nullable=False)
    status = db.Column(db.String(), default="open", nullable=False)

    creation_date = db.Column(
        db.DateTime(timezone=False), server_default=func.now(), nullable=False
    )

    def parse(self) -> dict:
        funders = []
        total_funding_amount = 0
        for funding in self.funding:
            funders.append(funding.parse())

            if funding.status == "submitted":
                total_funding_amount += funding.amount

        return {
            "project_id": self.project_identifier,
            "name": self.name,
            "creator": self.creator.parse(),
            "funders": funders,
            "total_funding_amount": total_funding_amount,
            "mediators": [mediator.parse() for mediator in self.mediators],
            "short_description": self.short_description,
            "long_description": self.long_description,
            "subjects": [subject.subject_name for subject in self.subjects],
            "deliverables": [
                deliverable.deliverable for deliverable in self.deliverables
            ],
            "days_to_complete": self.days_to_complete,
        }
