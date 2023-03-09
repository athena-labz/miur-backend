import uuid

from . import db

from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, func


class Submission(db.Model):
    __tablename__ = "submission"

    id = db.Column(db.Integer, primary_key=True)
    submission_identifier = db.Column(
        db.String(64), default=lambda: str(uuid.uuid4()), nullable=False
    )

    project_id = db.Column(db.Integer, ForeignKey("project.id"), nullable=False)
    project = relationship("Project", back_populates="submissions")

    review = relationship("Review", back_populates="submission", uselist=False)

    title = db.Column(db.String(), nullable=False)
    content = db.Column(db.String(), nullable=False)

    creation_date = db.Column(
        db.DateTime(timezone=False), server_default=func.now(), nullable=False
    )

    def parse(self) -> dict:
        return {
            "submission_id": self.submission_identifier,
            "project_id": self.project.project_identifier,
            "title": self.title,
            "content": self.content,
            "review": self.review.parse() if self.review is not None else None,
        }
