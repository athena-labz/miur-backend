from __future__ import annotations

import sys

from fixtures import api


def test_get_projects(api):
    client, app = api

    sys.path.append("src")

    from model import db, Project, User, Subject, Deliverable

    user_1 = User()
    user_1.address = "addr_test123"
    user_1.public_key_hash = "pubkey123"

    user_2 = User()
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


def test_create_project(api):
    client, app = api

    sys.path.append("src")

    from model import db, Project, User, Subject, Deliverable

    response = client.post("/projects/create", json={
        "name": "Project",
        "creator_address": "addr_test123",
        "short_description": "lorem ipsum...",
        "long_description": "lorem ipsum dolor sit amet...",
        "subjects": ["Math", "Tourism"],
        "reward_requested": 50,
        "days_to_complete": 15,
        "collateral": 130,
        "deliverables": ["I'm gonna do real good", "Trust me bro"]
    })

    assert response.status_code == 200
    assert response.json == {"success": True}

    projects = Project.query.all()
    assert len(projects) == 1

    # Make sure project created is equal to the sample provided
    project: Project = projects[0]
    assert project.name == "Project"

    assert project.creator.address == "addr_test123"

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
    user_1.address = "addr_test123"
    user_1.public_key_hash = "pubkey123"

    user_2 = User()
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