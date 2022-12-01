import uuid
import datetime
import string
import random

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
    created_quizes = relationship("Quiz", back_populates="creator")
    quiz_assignments = relationship("QuizAssignment", back_populates="assignee")
    mediated_projects = relationship(
        "Project", secondary=association_table, back_populates="mediators"
    )
    funding = relationship("Funding", back_populates="funder")

    creation_date = db.Column(
        db.DateTime(timezone=False), server_default=func.now(), nullable=False
    )

    @staticmethod
    def find(stake_address: str):
        return User.query.filter(User.stake_address == stake_address).first()

    @staticmethod
    def sample(
        stake_address: str = -1,
        email: str = -1,
        payment_address: str = -1,
        nft_identifier_policy: str = -1,
        created_projects: list = -1,
        created_quizes: list = -1,
        quiz_assignments: list = -1,
        mediated_projects: list = -1,
        funding: list = -1,
        creation_date: datetime.datetime = -1,
    ):
        def if_else(if_val, else_val):
            return if_val if if_val != -1 else else_val

        random_string = ''.join([random.choice(list("0123456789abcdef")) for i in range(8)])

        return User(
            stake_address=if_else(stake_address, f"stake_test{random_string}"),
            email=if_else(email, "alice@email.com"),
            payment_address=if_else(payment_address, "addr_test123"),
            nft_identifier_policy=if_else(
                nft_identifier_policy, f"nft_identifier_policy_{random_string}"
            ),
            created_projects=if_else(created_projects, []),
            created_quizes=if_else(created_quizes, []),
            quiz_assignments=if_else(quiz_assignments, []),
            mediated_projects=if_else(mediated_projects, []),
            funding=if_else(funding, []),
            creation_date=if_else(creation_date, datetime.datetime.utcnow()),
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
