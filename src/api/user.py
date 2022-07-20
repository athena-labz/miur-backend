from __future__ import annotations

from flask import request
from sqlalchemy import or_

from lib import cardano_tools
from model import User, db

import datetime
import logging


def validate_signature(signature, address):
    validation = cardano_tools.signature_message(signature, address)

    if validation is None:
        print(
            "Validation failed - Either address is incorrect or signature is invalid")
        return False

    if not validation.startswith("Athena MIUR | ") and len(validation) < 14:
        print(
            "Signature is formatted incorrectly - does not start with \"Athena MIUR | \" or does not have a continuation")
        return False

    try:
        timestamp = int(validation[14:])
    except ValueError:
        print("Invalid timestamp given - cannot convert to integer")
        return False

    current_date_unix = int(
        (datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

    print(abs(current_date_unix - timestamp))
    if abs(current_date_unix - timestamp) > 60:
        print("Invalid timestamp given - timestamp outside of the 60 seconds range")
        return False

    return True


def register(address: str):
    data = request.json

    existing_user: User | None = User.query.filter(
        or_(User.address == address, User.nickname == data["nickname"])).first()

    if existing_user is not None:
        if existing_user.address == address:
            return {
                "success": False,
                "message": f"User with address {address} already exists"
            }, 400
        else:
            return {
                "success": False,
                "message": f"User with nickname {data['nickname']} already exists"
            }, 400

    if "signature_plus_key" in data:
        if not validate_signature(data["signature_plus_key"], address):
            return {
                "success": False,
                "message": "Invalid signature"
            }, 400
    elif "signature" in data and "key" in data:
        if not validate_signature({"signature": data["signature"], "key": data["key"]}, address):
            return {
                "success": False,
                "message": "Invalid signature"
            }, 400
    else:
        return {
            "success": False,
            "message": "Signature not provided"
        }

    user = User()
    user.address = address
    user.public_key_hash = cardano_tools.address_to_pubkeyhash(address)

    user.nickname = data["nickname"]

    db.session.add(user)
    db.session.commit()

    return {"success": True}, 200
