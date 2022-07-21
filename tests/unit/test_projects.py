from __future__ import annotations

import sys
import datetime

from fixtures import api


def test_get_projects(api):
    client, app = api

    sys.path.append("src")

    from model import db, Project, User, Subject, Deliverable

    user_1 = User()
    user_1.nickname = "fastandfury"
    user_1.address = "addr_test123"
    user_1.public_key_hash = "pubkey123"

    user_2 = User()
    user_2.nickname = "arsene"
    user_2.address = "addr_test456"
    user_2.public_key_hash = "pubkey456"

    subject_1 = Subject()
    subject_1.subject_name = "Math"

    subject_2 = Subject()
    subject_2.subject_name = "Tourism"

    deliverable_1 = Deliverable()
    deliverable_1.deliverable = "I am going to do it"

    deliverable_2 = Deliverable()
    deliverable_2.deliverable = "I am doint it I swear"

    project_1 = Project()
    project_1.creator = user_1
    project_1.subjects = [subject_1, subject_2]

    project_1.name = "Project"

    project_1.short_description = "lorem ipsum..."
    project_1.long_description = "lorem ipsum dolor sit amet..."

    project_1.reward_requested = 50
    project_1.days_to_complete = 15
    project_1.collateral = 130

    project_1.deliverables = [deliverable_1, deliverable_2]
    project_1.mediators = [user_1, user_2]

    with app.app_context():
        db.session.add(project_1)

        db.session.add(user_1)
        db.session.add(user_2)

        db.session.add(subject_1)
        db.session.add(subject_2)

        db.session.add(deliverable_1)
        db.session.add(deliverable_2)

        db.session.commit()

        db.session.refresh(project_1)

        db.session.refresh(user_1)
        db.session.refresh(user_2)

        db.session.refresh(subject_1)
        db.session.refresh(subject_2)

        db.session.refresh(deliverable_1)
        db.session.refresh(deliverable_2)

    response = client.get("/projects")

    assert response.status_code == 200
    assert response.json == {
        "count": 1,
        "projects": [{
            "project_id": project_1.project_identifier,
            "name": "Project",
            "creator_address": "addr_test123",
            "short_description": "lorem ipsum...",
            "subjects": ["Math", "Tourism"],
            "reward_requested": 50,
            "days_to_complete": 15,
            "collateral": 130,
        }]
    }


def test_create_project(api, monkeypatch):
    client, app = api

    class NewDate(datetime.datetime):
        @classmethod
        def utcnow(cls):
            return cls(2022, 1, 1, 0, 0, 0)

    monkeypatch.setattr(
        "api.user.datetime.datetime",
        NewDate,
    )

    sys.path.append("src")

    from model import db, Project, User, Subject, Deliverable

    # Creator does not exist
    response = client.post("/projects/create", json={
        "name": "Project",
        "creator_address": "addr_test1qzhrrg588mzw38283mhqzdl35swuvhqmgqezf2x2l2zmkhaxf2ssp8g0zphaws48nmnghkd9lkq4l7jc04ks4f5vk50qdf28fq",
        "short_description": "lorem ipsum...",
        "long_description": "lorem ipsum dolor sit amet...",
        "subjects": ["Math", "Tourism"],
        "reward_requested": 50,
        "days_to_complete": 15,
        "collateral": 130,
        "deliverables": ["I'm gonna do real good", "Trust me bro"],
        "signature": "84584da301276761646472657373581d60ae31a2873ec4e89d478eee0137f1a41dc65c1b403224a8cafa85bb5f045820bff6dc39c2dd5684cd3015a65e9ea26ee1b3aa950b7de442c2dec9c289733e76a166686173686564f45818417468656e61204d495552207c20313634303939353230305840a50410fcb800b8ea4318ebce8ebf259e05e95a74d014fd954439777d7237c26fded71f4b71c15dc0f64014645f8ffdcb1b12b4dc003246073544d6142739f10a"
    })

    assert response.status_code == 400

    assert "success" in response.json
    assert response.json["success"] is False

    # Create user
    user = User()
    user.nickname = "blahblah"
    user.address = "addr_test1qzhrrg588mzw38283mhqzdl35swuvhqmgqezf2x2l2zmkhaxf2ssp8g0zphaws48nmnghkd9lkq4l7jc04ks4f5vk50qdf28fq"
    user.public_key_hash = "pubkey123"

    with app.app_context():
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)

    # Signature is not valid
    response = client.post("/projects/create", json={
        "name": "Project",
        "creator_address": "addr_test1qzhrrg588mzw38283mhqzdl35swuvhqmgqezf2x2l2zmkhaxf2ssp8g0zphaws48nmnghkd9lkq4l7jc04ks4f5vk50qdf28fq",
        "short_description": "lorem ipsum...",
        "long_description": "lorem ipsum dolor sit amet...",
        "subjects": ["Math", "Tourism"],
        "reward_requested": 50,
        "days_to_complete": 15,
        "collateral": 130,
        "deliverables": ["I'm gonna do real good", "Trust me bro"],
        "signature": "84584da301276761646472657373581d6045979b6a06fc37fffdb901304d5c970b08217b4e17b749be604b6c9704582067eef9883bd41729d2b2e26cc095e2ada32ddeee4529352e7a8d41810ed2800fa166686173686564f45818417468656e61204d495552207c203136343039393532303058408963af15e0fa9c22ccf8320712f7787d732eab1aa6976b4caa5400bcb6ba5b4e9eb0d9a46278bf3a78a36d6bbcfb7a6b6403f9128e3c00a5c955e0d33443ba00"
    })

    assert response.status_code == 400

    assert "success" in response.json
    assert response.json["success"] is False

    # Creator does exist
    response = client.post("/projects/create", json={
        "name": "Project",
        "creator_address": "addr_test1qzhrrg588mzw38283mhqzdl35swuvhqmgqezf2x2l2zmkhaxf2ssp8g0zphaws48nmnghkd9lkq4l7jc04ks4f5vk50qdf28fq",
        "short_description": "lorem ipsum...",
        "long_description": "lorem ipsum dolor sit amet...",
        "subjects": ["Math", "Tourism"],
        "reward_requested": 50,
        "days_to_complete": 15,
        "collateral": 130,
        "deliverables": ["I'm gonna do real good", "Trust me bro"],
        "signature": "84584da301276761646472657373581d60ae31a2873ec4e89d478eee0137f1a41dc65c1b403224a8cafa85bb5f045820bff6dc39c2dd5684cd3015a65e9ea26ee1b3aa950b7de442c2dec9c289733e76a166686173686564f45818417468656e61204d495552207c20313634303939353230305840a50410fcb800b8ea4318ebce8ebf259e05e95a74d014fd954439777d7237c26fded71f4b71c15dc0f64014645f8ffdcb1b12b4dc003246073544d6142739f10a"
    })

    assert response.status_code == 200
    assert response.json == {"success": True}

    projects = Project.query.all()
    assert len(projects) == 1

    # Make sure project created is equal to the sample provided
    project: Project = projects[0]
    assert project.name == "Project"

    assert project.creator.address == "addr_test1qzhrrg588mzw38283mhqzdl35swuvhqmgqezf2x2l2zmkhaxf2ssp8g0zphaws48nmnghkd9lkq4l7jc04ks4f5vk50qdf28fq"

    assert project.short_description == "lorem ipsum..."
    assert project.long_description == "lorem ipsum dolor sit amet..."

    assert set([subject.subject_name for subject in project.subjects]) == {
        "Math", "Tourism"}

    assert project.reward_requested == 50
    assert project.days_to_complete == 15
    assert project.collateral == 130

    assert set([deliverable.deliverable for deliverable in project.deliverables]) == {
        "I'm gonna do real good", "Trust me bro"}


def test_get_projects(api):
    client, app = api

    sys.path.append("src")

    from model import db, Project, User, Subject, Deliverable

    user_1 = User()
    user_1.nickname = "fastandfury"
    user_1.address = "addr_test123"
    user_1.public_key_hash = "pubkey123"

    user_2 = User()
    user_2.nickname = "arsene"
    user_2.address = "addr_test456"
    user_2.public_key_hash = "pubkey456"

    subject_1 = Subject()
    subject_1.subject_name = "Math"

    subject_2 = Subject()
    subject_2.subject_name = "Tourism"

    deliverable_1 = Deliverable()
    deliverable_1.deliverable = "I am going to do it"

    deliverable_2 = Deliverable()
    deliverable_2.deliverable = "I am doint it I swear"

    project_1 = Project()
    project_1.creator = user_1
    project_1.subjects = [subject_1, subject_2]

    project_1.name = "Project"

    project_1.short_description = "lorem ipsum..."
    project_1.long_description = "lorem ipsum dolor sit amet..."

    project_1.reward_requested = 50
    project_1.days_to_complete = 15
    project_1.collateral = 130

    project_1.deliverables = [deliverable_1, deliverable_2]
    project_1.mediators = [user_1, user_2]

    with app.app_context():
        db.session.add(project_1)

        db.session.add(user_1)
        db.session.add(user_2)

        db.session.add(subject_1)
        db.session.add(subject_2)

        db.session.add(deliverable_1)
        db.session.add(deliverable_2)

        db.session.commit()

        db.session.refresh(project_1)

        db.session.refresh(user_1)
        db.session.refresh(user_2)

        db.session.refresh(subject_1)
        db.session.refresh(subject_2)

        db.session.refresh(deliverable_1)
        db.session.refresh(deliverable_2)

    response = client.get(f"/projects/{project_1.project_identifier}")

    assert response.status_code == 200
    assert response.json == {
        "success": True,
        "project": {
            "name": "Project",
            "creator_address": "addr_test123",
            "short_description": "lorem ipsum...",
            "long_description": "lorem ipsum dolor sit amet...",
            "subjects": ["Math", "Tourism"],
            "reward_requested": 50,
            "days_to_complete": 15,
            "collateral": 130,
            "deliverables": ["I am going to do it", "I am doint it I swear"],
            "mediators": ["addr_test123", "addr_test456"]
        }
    }
