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
            return cls(2022, 1, 1, 0, 0, 0)

    monkeypatch.setattr(
        "api.user.datetime.datetime",
        NewDate,
    )

    from model import db, User

    address = "addr_test1qzhrrg588mzw38283mhqzdl35swuvhqmgqezf2x2l2zmkhaxf2ssp8g0zphaws48nmnghkd9lkq4l7jc04ks4f5vk50qdf28fq"
    response = client.post(f"/register/{address}", json={
        "nickname": "zKeanuReevesHD65",
        "signature": "84584da301276761646472657373581d60ae31a2873ec4e89d478eee0137f1a41dc65c1b403224a8cafa85bb5f045820bff6dc39c2dd5684cd3015a65e9ea26ee1b3aa950b7de442c2dec9c289733e76a166686173686564f45818417468656e61204d495552207c20313634303939353230305840a50410fcb800b8ea4318ebce8ebf259e05e95a74d014fd954439777d7237c26fded71f4b71c15dc0f64014645f8ffdcb1b12b4dc003246073544d6142739f10a"
    })

    assert response.status_code == 200
    assert response.json == {"success": True}

    users = User.query.all()
    assert len(users) == 1

    user: User = users[0]
    assert user.address == address
    assert user.public_key_hash == "ae31a2873ec4e89d478eee0137f1a41dc65c1b403224a8cafa85bb5f"
    assert user.nickname == "zKeanuReevesHD65"

    db.session.delete(user)
    db.session.commit()

    # Test registering with different format
    address = "addr_test1qzhrrg588mzw38283mhqzdl35swuvhqmgqezf2x2l2zmkhaxf2ssp8g0zphaws48nmnghkd9lkq4l7jc04ks4f5vk50qdf28fq"
    response = client.post(f"/register/{address}", json={
        "nickname": "zKeanuReevesHD65",
        "signature": {
            "signature": "84582aa201276761646472657373581d60ae31a2873ec4e89d478eee0137f1a41dc65c1b403224a8cafa85bb5fa166686173686564f45818417468656e61204d495552207c203136343039393532303058402a7ca5f3e2f115d8e40bbea5d30624a14def3c45944c66f0f40541f6590366396353669f38c4129b62db9c410586803b289a4acf8cbf6cd8c3e5c0adfdf7d909",
            "key": "a4010103272006215820bff6dc39c2dd5684cd3015a65e9ea26ee1b3aa950b7de442c2dec9c289733e76"
        }
    })

    assert response.status_code == 200
    assert response.json == {"success": True}

    users = User.query.all()
    assert len(users) == 1

    user: User = users[0]
    assert user.address == address
    assert user.public_key_hash == "ae31a2873ec4e89d478eee0137f1a41dc65c1b403224a8cafa85bb5f"
    assert user.nickname == "zKeanuReevesHD65"

    # User with timestamp too high
    address = "addr_test1qpze0xm2qm7r0llahyqnqn2uju9ssgtmfctmwjd7vp9ke9lnplxya9mu0tlt38h0al3j0fxhuu0gwee80un4gg25zvsq5nwmd7"
    response = client.post(f"/register/{address}", json={
        "nickname": "khabib",
        "signature": "84584da301276761646472657373581d6045979b6a06fc37fffdb901304d5c970b08217b4e17b749be604b6c9704582067eef9883bd41729d2b2e26cc095e2ada32ddeee4529352e7a8d41810ed2800fa166686173686564f45818417468656e61204d495552207c203136343039393532363158406d45ae0a6835702024a36d98f70770d89f620d07fa5065252c21c9bb8369c9cb72d0ee4f16c1901f5b99497861c5d953865009a594c854f13e4c4b5c8828b906"
    })

    assert response.status_code == 400

    assert "success" in response.json
    assert response.json["success"] is False

    # User with timestamp too low
    address = "addr_test1qpze0xm2qm7r0llahyqnqn2uju9ssgtmfctmwjd7vp9ke9lnplxya9mu0tlt38h0al3j0fxhuu0gwee80un4gg25zvsq5nwmd7"
    response = client.post(f"/register/{address}", json={
        "nickname": "khabib",
        "signature": "84584da301276761646472657373581d6045979b6a06fc37fffdb901304d5c970b08217b4e17b749be604b6c9704582067eef9883bd41729d2b2e26cc095e2ada32ddeee4529352e7a8d41810ed2800fa166686173686564f45818417468656e61204d495552207c203136343039393531333958406addac1c89d30c3a8d86a14a9f5efbafd77c4cc52cc4d77b0b8a0caefff5bccbdc81f44f834a78ef9f24571f243ecd955aad7d7590409731d4bbdea8d5ebee0d"
    })

    assert response.status_code == 400

    assert "success" in response.json
    assert response.json["success"] is False

    # Try to create user with same address
    address = "addr_test1qzhrrg588mzw38283mhqzdl35swuvhqmgqezf2x2l2zmkhaxf2ssp8g0zphaws48nmnghkd9lkq4l7jc04ks4f5vk50qdf28fq"
    response = client.post(f"/register/{address}", json={
        "nickname": "khabib",
        "signature": "84584da301276761646472657373581d60ae31a2873ec4e89d478eee0137f1a41dc65c1b403224a8cafa85bb5f045820bff6dc39c2dd5684cd3015a65e9ea26ee1b3aa950b7de442c2dec9c289733e76a166686173686564f45818417468656e61204d495552207c20313634303939353230305840a50410fcb800b8ea4318ebce8ebf259e05e95a74d014fd954439777d7237c26fded71f4b71c15dc0f64014645f8ffdcb1b12b4dc003246073544d6142739f10a"
    })

    assert response.status_code == 400

    assert "success" in response.json
    assert response.json["success"] is False

    # Try to create user with same nickname
    address = "addr_test1qpze0xm2qm7r0llahyqnqn2uju9ssgtmfctmwjd7vp9ke9lnplxya9mu0tlt38h0al3j0fxhuu0gwee80un4gg25zvsq5nwmd7"
    response = client.post(f"/register/{address}", json={
        "nickname": "zKeanuReevesHD65",
        "signature": "84584da301276761646472657373581d6045979b6a06fc37fffdb901304d5c970b08217b4e17b749be604b6c9704582067eef9883bd41729d2b2e26cc095e2ada32ddeee4529352e7a8d41810ed2800fa166686173686564f45818417468656e61204d495552207c203136343039393532303058408963af15e0fa9c22ccf8320712f7787d732eab1aa6976b4caa5400bcb6ba5b4e9eb0d9a46278bf3a78a36d6bbcfb7a6b6403f9128e3c00a5c955e0d33443ba00"
    })

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

    user = User()
    user.nickname = "Nick"
    user.address = "addr_test123"
    user.public_key_hash = "abc123"

    with app.app_context():
        db.session.add(user)
        db.session.commit()

    response = client.get("/user/addr_test123")

    assert response.status_code == 200
    assert response.json == {
        "nickname": "Nick",
        "public_key_hash": "abc123"
    }

    response = client.get("/user/addr_test456")

    assert response.status_code == 404