import datetime
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

    submission_id = db.Column(db.Integer, ForeignKey("submission.id"), nullable=False)
    submission = relationship("Submission", back_populates="review")

    approval = db.Column(db.Boolean, nullable=False)
    review = db.Column(db.String(), nullable=False)
    deadline = db.Column(db.DateTime(timezone=False), nullable=True)

    creation_date = db.Column(
        db.DateTime(timezone=False), server_default=func.now(), nullable=False
    )

    def parse(self) -> dict:
        return {
            "review_id": self.review_identifier,
            "submission_id": self.submission.submission_identifier,
            "reviewer": self.reviewer.parse(),
            "approval": self.approval,
            "review": self.review,
            "deadline": int(
                (self.deadline - datetime.datetime(1970, 1, 1)).total_seconds()
            ) if self.deadline else None,
        }
