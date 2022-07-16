import uuid

from . import db

from sqlalchemy.orm import relationship
from sqlalchemy import func


def str_uuid():
    return str(uuid.uuid4())


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    user_identifier = db.Column(
        db.String(64), default=str_uuid, nullable=False)

    user_address = db.Column(db.String(), nullable=False)
    user_public_key_hash = db.Column(db.String(), nullable=False)

    created_projects = relationship("Project", back_populates="proposer")
    user_funding = relationship("Fund", back_populates="funder")

    creation_date = db.Column(db.DateTime(
        timezone=False), server_default=func.now(), nullable=False)
