from __future__ import annotations

from flask import request
from sqlalchemy import or_

from lib import cardano_tools, auth_tools
from model import User, db

import datetime
import logging


def register(address: str):
    data = request.json

    existing_user: User | None = User.query.filter(
        or_(User.address == address, User.email == data["email"])
    ).first()

    if existing_user is not None:
        if existing_user.address == address:
            return {
                "success": False,
                "message": f"User with address {address} already exists",
                "code": "address-exists",
            }, 400
        else:
            return {
                "success": False,
                "message": f"User with email {data['email']} already exists",
                "code": "email-exists",
            }, 400

    if not auth_tools.validate_signature(data["signature"], address):
        return {
            "success": False,
            "message": "Invalid signature",
            "code": "invalid-signature",
        }, 400

    user = User()
    user.address = address
    user.email = data["email"]

    db.session.add(user)
    db.session.commit()

    return {"success": True}, 200


def get_info(address: str):
    user: User | None = User.query.filter(User.address == address).first()

    if user is None:
        return {
            "success": False,
            "message": f"Could not find address {address}",
            "code": "address-not-found",
        }, 404

    return {
        "id": user.user_identifier,
        "address": user.address,
        "email": user.email,
        **(
            {"nft_identifier_policy": user.nft_identifier_policy}
            if user.nft_identifier_policy is not None
            else {}
        ),
    }
