import uuid
import string
import random
import hashlib

from . import db

from sqlalchemy.orm import relationship
from sqlalchemy import func


def str_uuid():
    return str(uuid.uuid4())


def generate_salt(length=16):
    characters = string.ascii_letters + string.digits

    return "".join(random.choice(characters) for _ in range(length))


def hash_password(password: str, salt: str):
    salted_password = salt.encode("utf-8")
    return hashlib.scrypt(
        password.encode("utf-8"), salt=salted_password, n=16384, r=8, p=1, dklen=64
    ).hex()


class ProdUser(db.Model):
    __tablename__ = "prod_user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(), nullable=False, unique=True)

    salt = db.Column(db.String(), nullable=False)
    password_hash = db.Column(db.String(), nullable=False)

    stake_address = db.Column(db.String())
    payment_address = db.Column(db.String())

    is_email_verified = db.Column(db.Boolean(), default=False)
    is_address_verified = db.Column(db.Boolean(), default=False)

    creation_date = db.Column(
        db.DateTime(timezone=False), server_default=func.now(), nullable=False
    )

    @staticmethod
    def login(email: str, password: str):
        user = ProdUser.query.filter_by(email=email).first()

        if not user:
            return None

        password_hash = hash_password(password, user.salt)

        if password_hash != user.password_hash:
            return None

        return user

    @staticmethod
    def register(email: str, password: str):
        salt = generate_salt()
        password_hash = hash_password(password, salt)

        user = ProdUser(
            email=email,
            salt=salt,
            password_hash=password_hash,
        )

        db.session.add(user)
        db.session.commit()

        return user
