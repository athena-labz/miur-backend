import uuid

from . import db

from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, func


class Review(db.Model):
    __tablename__ = "review"

    id = db.Column(db.Integer, primary_key=True)
    review_identifier = db.Column(
        db.String(64), default=lambda: str(uuid.uuid4()), nullable=False
    )

    reviewer_id = db.Column(db.Integer, ForeignKey("user.id"), nullable=False)
    reviewer = relationship("User", back_populates="reviews")

    project_id = db.Column(db.Integer, ForeignKey("project.id"), nullable=False)
    project = relationship("Project", back_populates="reviews")

    approval = db.Column(db.Boolean, nullable=False)
    review = db.Column(db.String(), nullable=False)
    deadline = db.Column(db.DateTime(timezone=False), nullable=False)

    creation_date = db.Column(
        db.DateTime(timezone=False), server_default=func.now(), nullable=False
    )

    def parse(self) -> dict:
        return {
            "review_id": self.review_identifier,
            "project_id": self.project.project_identifier,
            "approval": self.approval,
            "review": self.review,
            "deadline": self.deadline,
            "creation_date": self.creation_date,
        }
