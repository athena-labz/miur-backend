import uuid

from . import db

from sqlalchemy.orm import relationship
from sqlalchemy import func

from model.project_mediator_association import association_table


def str_uuid():
    return str(uuid.uuid4())


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    user_identifier = db.Column(
        db.String(64), default=str_uuid, nullable=False)

    # This is optional, but is required to do certain action
    user_nft_policy = db.Column(db.String(56))

    nickname = db.Column(db.String(), nullable=False)

    address = db.Column(db.String(), nullable=False)
    public_key_hash = db.Column(db.String(), nullable=False)

    created_projects = relationship("Project", back_populates="creator")
    mediated_projects = relationship(
        "Project", secondary=association_table, back_populates="mediators")

    creation_date = db.Column(db.DateTime(
        timezone=False), server_default=func.now(), nullable=False)
