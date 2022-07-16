from . import db

from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, func


class Fund(db.Model):
    __tablename__ = "fund"

    id = db.Column(db.Integer, primary_key=True)

    funder_id = db.Column(db.Integer, ForeignKey(
        "user.id"), nullable=False)
    funder = relationship("User", back_populates="user_funding")

    project_id = db.Column(db.Integer, ForeignKey(
        "project.id"), nullable=False)
    project = relationship("Project", back_populates="project_funding")

    funding_amount = db.Column(db.Integer, nullable=False)

    tx_hash = db.Column(db.String(64))

    # draft, submitted, on-chain, invalid
    status = db.Column(db.String(), nullable=False)

    creation_date = db.Column(db.DateTime(
        timezone=False), server_default=func.now(), nullable=False)
