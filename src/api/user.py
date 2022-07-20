from __future__ import annotations

from flask import request
from sqlalchemy import or_

from lib import cardano_tools
from model import User, db


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
    
    user = User()
    user.address = address
    user.public_key_hash = cardano_tools.address_to_pubkeyhash(address)

    user.nickname = data["nickname"]

    db.session.add(user)
    db.session.commit()

    return {"success": True}, 200
