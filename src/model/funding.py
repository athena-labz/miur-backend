import uuid

from . import db

from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, func


class Funding(db.Model):
    __tablename__ = "funding"

    id = db.Column(db.Integer, primary_key=True)

    funder_id = db.Column(db.Integer, ForeignKey("user.id"), nullable=False)
    funder = relationship("User", back_populates="funding")

    project_id = db.Column(db.Integer, ForeignKey(
        "project.id"), nullable=False)
    project = relationship("Project", back_populates="funding")

    transaction_hash = db.Column(db.String(), nullable=False, unique=True)

    # requested, submitted, on-chain, expired
    status = db.Column(db.String(), default="requested", nullable=False)

    creation_date = db.Column(db.DateTime(
        timezone=False), server_default=func.now(), nullable=False)
    update_date = db.Column(db.DateTime(timezone=False), onupdate=func.now())
