from __future__ import annotations

import sys
import datetime

from fixtures import api


def test_register(api, monkeypatch):
    client, app = api

    sys.path.append("src")

    class NewDate(datetime.datetime):
        @classmethod
        def utcnow(cls):
            return cls(2022, 11, 12, 10, 15, 0)

    monkeypatch.setattr(
        "api.user.datetime.datetime",
        NewDate,
    )

    from model import db, User

    stake_address = "stake_test1uzny4ggqn583qm7hg2neae5tmxjlmq2llfv86mg256xt28sv20c2r"
    payment_address = "addr_test1vzhrrg588mzw38283mhqzdl35swuvhqmgqezf2x2l2zmkhckw4f7n"

    response = client.post(
        f"/register/{stake_address}",
        json={
            "email": "hallo@email.com",
            "payment_address": payment_address,
            "signature": "84584da301276761646472657373581d60a64aa1009d0f106fd742a79ee68bd9a5fd815ffa587d6d0aa68cb51e045820f84f04c0054dbbb0a7fcbd1584dac460cbd1b14723a6e9d2571477ba21644858a166686173686564f45818417468656e61204d495552207c2031363638323538353834584020bd7dfdf5d6759193e5a63004949bbb116b702f5e6a334394b55937921bc060e762d7101b1e7200aa53cd6c0e2e373842eb79d20bff063e7c03630d66665a03",
        },
    )

    assert response.status_code == 200
    assert response.json == {"success": True}

    users = User.query.all()
    assert len(users) == 1

    user: User = users[0]
    assert user.stake_address == stake_address
    assert user.payment_address == payment_address
    assert user.email == "hallo@email.com"

    db.session.delete(user)
    db.session.commit()

    # Test registering with different format
    response = client.post(
        f"/register/{stake_address}",
        json={
            "email": "hallo@email.com",
            "payment_address": payment_address,
            "signature": {
                "signature": "84582aa201276761646472657373581d60a64aa1009d0f106fd742a79ee68bd9a5fd815ffa587d6d0aa68cb51ea166686173686564f45818417468656e61204d495552207c203136363832353835383458403de26196046172fa4dcc3b88e106daa92ac4fc5ccee3be157fea3626136545561518d89f81f6f4fc7be100c7c24c9ffc7d35314626f157db3960eccf0f19270a",
                "key": "a4010103272006215820f84f04c0054dbbb0a7fcbd1584dac460cbd1b14723a6e9d2571477ba21644858",
            },
        },
    )

    assert response.status_code == 200
    assert response.json == {"success": True}

    users = User.query.all()
    assert len(users) == 1

    user: User = users[0]
    assert user.stake_address == stake_address
    assert user.payment_address == payment_address
    assert user.email == "hallo@email.com"

    db.session.delete(user)
    db.session.commit()

    # User with timestamp too high
    response = client.post(
        f"/register/{stake_address}",
        json={
            "email": "khabib@email.com",
            "payment_address": payment_address,
            "signature": "84584da301276761646472657373581d60a64aa1009d0f106fd742a79ee68bd9a5fd815ffa587d6d0aa68cb51e045820f84f04c0054dbbb0a7fcbd1584dac460cbd1b14723a6e9d2571477ba21644858a166686173686564f45818417468656e61204d495552207c20323137333139313033395840e89b78d5d4db2a1669b7be9505ae241f954886baa7162a54e2c57b5c891326bb478a68d27efb6876d8399c78fad59f7ba920e19be29b978001f9401724ad7602",
        },
    )

    assert response.status_code == 400

    assert "success" in response.json
    assert response.json["success"] is False

    # User with timestamp too low
    response = client.post(
        f"/register/{stake_address}",
        json={
            "email": "khabib@email.com",
            "payment_address": payment_address,
            "signature": "84584da301276761646472657373581d60a64aa1009d0f106fd742a79ee68bd9a5fd815ffa587d6d0aa68cb51e045820f84f04c0054dbbb0a7fcbd1584dac460cbd1b14723a6e9d2571477ba21644858a166686173686564f457417468656e61204d495552207c203738343635333033395840162ccf5a93ece2eca80aa6e2e657e9823f9a4afbd20bd6d1453a318ef73c652e1ed6f93ff6c54a03f85285e72a5505e403b363cb0476e9d7b48f9d721f0ea205",
        },
    )

    assert response.status_code == 400

    assert "success" in response.json
    assert response.json["success"] is False

    # Try to create user with same address
    user = User(
        email="alice@email.com",
        stake_address=stake_address,
        payment_address="addr_test123",
    )

    db.session.add(user)
    db.session.commit()

    response = client.post(
        f"/register/{stake_address}",
        json={
            "email": "khabib@email.com",
            "payment_address": "addr_test456",
            "signature": "84584da301276761646472657373581d60ae31a2873ec4e89d478eee0137f1a41dc65c1b403224a8cafa85bb5f045820bff6dc39c2dd5684cd3015a65e9ea26ee1b3aa950b7de442c2dec9c289733e76a166686173686564f45818417468656e61204d495552207c20313634303939353230305840a50410fcb800b8ea4318ebce8ebf259e05e95a74d014fd954439777d7237c26fded71f4b71c15dc0f64014645f8ffdcb1b12b4dc003246073544d6142739f10a",
        },
    )

    assert response.status_code == 400

    assert "success" in response.json
    assert response.json["success"] is False


def test_get_user(api, monkeypatch):
    client, app = api

    sys.path.append("src")

    class NewDate(datetime.datetime):
        @classmethod
        def utcnow(cls):
            return cls(2022, 1, 1, 0, 0, 0)

    monkeypatch.setattr(
        "api.user.datetime.datetime",
        NewDate,
    )

    from model import db, User

    user = User(
        email="nick@email.com",
        stake_address="stake_test123",
        payment_address="addr_test123",
        nft_identifier_policy = "policy123"
    )

    with app.app_context():
        db.session.add(user)
        db.session.commit()

    response = client.get("/user/stake_test123")

    assert response.status_code == 200
    assert response.json == {
        "email": "nick@email.com",
        "payment_address": "addr_test123",
        "stake_address": "stake_test123",
        "nft_identifier_policy": "policy123",
    }

    response = client.get("/user/addr_test456")

    assert response.status_code == 404
