from __future__ import annotations

import sys

from fixtures import api


def test_get_projects(api):
    client, app = api

    sys.path.append("src")

    from model import db, User

    address = "addr_test1qzhrrg588mzw38283mhqzdl35swuvhqmgqezf2x2l2zmkhaxf2ssp8g0zphaws48nmnghkd9lkq4l7jc04ks4f5vk50qdf28fq"
    response = client.post(f"/register/{address}", json={
        "nickname": "zKeanuReevesHD65"
    })

    assert response.status_code == 200
    assert response.json == {"success": True}

    users = User.query.all()
    assert len(users) == 1

    user: User = users[0]
    assert user.address == address
    assert user.public_key_hash == "ae31a2873ec4e89d478eee0137f1a41dc65c1b403224a8cafa85bb5f"
    assert user.nickname == "zKeanuReevesHD65"

    # Try to create user with same address
    address = "addr_test1qzhrrg588mzw38283mhqzdl35swuvhqmgqezf2x2l2zmkhaxf2ssp8g0zphaws48nmnghkd9lkq4l7jc04ks4f5vk50qdf28fq"
    response = client.post(f"/register/{address}", json={
        "nickname": "khabib"
    })

    assert response.status_code == 400

    assert "success" in response.json
    assert response.json["success"] is False

    # Try to create user with same nickname
    address = "addr_test1qrq365a7z6tch4q279hf6cnl56pzft89qnnk0hfxtc4s0zepn78rllhusgu4mu9leljw2ahclqjt4cx8xxlr2vsuq8tsn8c3dy"
    response = client.post(f"/register/{address}", json={
        "nickname": "zKeanuReevesHD65"
    })

    assert response.status_code == 400

    assert "success" in response.json
    assert response.json["success"] is False