from __future__ import annotations

from flask import request
from sqlalchemy import or_

from lib import cardano_tools, auth_tools
from model import User, db

import datetime
import logging


def register(stake_address: str):
    data = request.json

    existing_user: User | None = User.query.filter(
        User.stake_address == stake_address
    ).first()

    if existing_user is not None:
        return {
            "success": False,
            "message": f"User with stake address {stake_address} already exists",
            "code": "address-exists",
        }, 400

    if not auth_tools.validate_signature(data["signature"], stake_address):
        return {
            "success": False,
            "message": "Invalid signature",
            "code": "invalid-signature",
        }, 400

    user = User(
        stake_address=stake_address,
        payment_address=data["payment_address"],
        email=data["email"],
    )

    db.session.add(user)
    db.session.commit()
    db.session.refresh(user)

    return {"success": True}, 200


def get_info(stake_address: str):
    user: User | None = User.query.filter(User.stake_address == stake_address).first()

    if user is None:
        return {
            "success": False,
            "message": f"Could not find stake address {stake_address}",
            "code": "address-not-found",
        }, 404

    return {
        "stake_address": user.stake_address,
        "payment_address": user.payment_address,
        "email": user.email,
        **(
            {"nft_identifier_policy": user.nft_identifier_policy}
            if user.nft_identifier_policy is not None
            else {}
        ),
    }
