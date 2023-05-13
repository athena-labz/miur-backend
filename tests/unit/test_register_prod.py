from fixtures import api
from typing import List

import hashlib


def test_register(api):
    client, app = api

    from model import db, ProdUser

    email = "alice@email.com"
    password = "password"

    res = client.post(f"/prod/register/{email}", json={"password": password})

    assert res.status_code == 200

    users: List[ProdUser] = ProdUser.query.all()
    assert len(users) == 1

    user = users[0]

    assert user.email == email

    salted_password = user.salt.encode("utf-8")
    password_hash = hashlib.scrypt(
        password.encode("utf-8"), salt=salted_password, n=16384, r=8, p=1, dklen=64
    ).hex()

    assert user.password_hash == password_hash

    assert user.stake_address is None
    assert user.payment_address is None

    assert user.is_email_verified == False
    assert user.is_address_verified == False
