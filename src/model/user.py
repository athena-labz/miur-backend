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
    stake_address = db.Column(db.String(), nullable=False, unique=True)

    email = db.Column(db.String(), nullable=False)

    # This address is the one we are using for our operations
    payment_address = db.Column(db.String(), nullable=False)

    # NFT policy ID that will identify this user for the smart contracts
    nft_identifier_policy = db.Column(db.String(), unique=True)

    created_projects = relationship("Project", back_populates="creator")
    mediated_projects = relationship(
        "Project", secondary=association_table, back_populates="mediators"
    )
    funding = relationship("Funding", back_populates="funder")

    creation_date = db.Column(
        db.DateTime(timezone=False), server_default=func.now(), nullable=False
    )

    def parse(self) -> dict:
        return {
            "email": self.email,
            "payment_address": self.payment_address,
            "stake_address": self.stake_address,
            **(
                {"nft_identifier_policy": self.nft_identifier_policy}
                if self.nft_identifier_policy is not None
                else {}
            ),
        }
