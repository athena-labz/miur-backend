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

    email = db.Column(db.String(), nullable=False, unique=True)

    # This address is the one we are using for our operations
    # NFT identifier should be sent to this address
    address = db.Column(db.String(), nullable=False, unique=True)

    # NFT policy ID that will identify this user for the smart contracts
    nft_identifier_policy = db.Column(db.String(), unique=True)

    created_projects = relationship("Project", back_populates="creator")
    mediated_projects = relationship(
        "Project", secondary=association_table, back_populates="mediators")

    creation_date = db.Column(db.DateTime(
        timezone=False), server_default=func.now(), nullable=False)
