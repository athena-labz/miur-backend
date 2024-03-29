from __future__ import annotations

import sys
import datetime

from fixtures import api


def test_get_projects(api):
    client, app = api

    sys.path.append("src")

    from model import db, Project, User, Subject, Deliverable, Funding

    user_1 = User(
        email="bonjour@email.com",
        stake_address="stake_test123",
        payment_address="addr_test123",
    )

    user_2 = User(
        email="arsene@email.com",
        stake_address="stake_test456",
        payment_address="addr_test456",
    )

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

    project_1.days_to_complete = 15

    project_1.deliverables = [deliverable_1, deliverable_2]
    project_1.mediators = [user_1, user_2]

    funding = Funding(
        funder=user_2,
        project=project_1,
        transaction_hash="hash",
        transaction_index=0,
        amount=10_000_000,
        status="foobar",
    )

    with app.app_context():
        db.session.add(project_1)

        db.session.add(user_1)
        db.session.add(user_2)

        db.session.add(subject_1)
        db.session.add(subject_2)

        db.session.add(deliverable_1)
        db.session.add(deliverable_2)

        db.session.add(funding)

        db.session.commit()

        db.session.refresh(project_1)

        db.session.refresh(user_1)
        db.session.refresh(user_2)

        db.session.refresh(subject_1)
        db.session.refresh(subject_2)

        db.session.refresh(deliverable_1)
        db.session.refresh(deliverable_2)

        db.session.refresh(funding)

    parsed_project = {
        "project_id": project_1.project_identifier,
        "name": "Project",
        "creator": {
            "email": "bonjour@email.com",
            "payment_address": "addr_test123",
            "stake_address": "stake_test123",
        },
        "short_description": "lorem ipsum...",
        "long_description": "lorem ipsum dolor sit amet...",
        "subjects": ["Math", "Tourism"],
        "days_to_complete": 15,
        "funders": [
            {
                "user": {
                    "email": "arsene@email.com",
                    "payment_address": "addr_test456",
                    "stake_address": "stake_test456",
                },
                "amount": 10_000_000,
                "status": "foobar",
            }
        ],
        "total_funding_amount": 0,
        "mediators": [
            {
                "email": "bonjour@email.com",
                "payment_address": "addr_test123",
                "stake_address": "stake_test123",
            },
            {
                "email": "arsene@email.com",
                "payment_address": "addr_test456",
                "stake_address": "stake_test456",
            },
        ],
        "deliverables": ["I am going to do it", "I am doint it I swear"],
    }

    response = client.get("/projects")

    assert response.status_code == 200
    assert response.json == {
        "count": 1,
        "projects": [parsed_project],
    }

    # Filter by creator
    response = client.get("/projects?creator=stake_test123")

    assert response.status_code == 200
    assert response.json == {
        "count": 1,
        "projects": [parsed_project],
    }

    response = client.get("/projects?creator=stake_test456")

    assert response.status_code == 200
    assert response.json == {
        "count": 0,
        "projects": [],
    }

    # Filter by funder
    response = client.get("/projects?funder=stake_test456")

    assert response.status_code == 200
    assert response.json == {
        "count": 1,
        "projects": [parsed_project],
    }

    response = client.get("/projects?funder=stake_test123")

    assert response.status_code == 200
    assert response.json == {
        "count": 0,
        "projects": [],
    }

    # Filter by both creator and funder
    response = client.get("/projects?creator=stake_test123&funder=stake_test456")

    assert response.status_code == 200
    assert response.json == {
        "count": 1,
        "projects": [parsed_project],
    }

    response = client.get("/projects?creator=stake_test123&funder=stake_test789")

    assert response.status_code == 200
    assert response.json == {
        "count": 1,
        "projects": [parsed_project],
    }

    response = client.get("/projects?creator=stake_test789&funder=stake_test456")

    assert response.status_code == 200
    assert response.json == {
        "count": 1,
        "projects": [parsed_project],
    }

    response = client.get("/projects?creator=stake_test789&funder=stake_test789")

    assert response.status_code == 200
    assert response.json == {
        "count": 0,
        "projects": [],
    }


def test_create_project(api, monkeypatch):
    client, app = api

    class NewDate(datetime.datetime):
        @classmethod
        def utcnow(cls):
            return cls(2022, 11, 12, 10, 15, 0)

    monkeypatch.setattr(
        "api.user.datetime.datetime",
        NewDate,
    )

    sys.path.append("src")

    from model import db, Project, User, Subject, Deliverable

    # Creator does not exist
    response = client.post(
        "/projects/create",
        json={
            "name": "Project",
            "creator": "stake_test1uzny4ggqn583qm7hg2neae5tmxjlmq2llfv86mg256xt28sv20c2r",
            "short_description": "lorem ipsum...",
            "long_description": "lorem ipsum dolor sit amet...",
            "subjects": ["Math", "Tourism"],
            "days_to_complete": 15,
            "deliverables": ["I'm gonna do real good", "Trust me bro"],
            "mediators": [],
            "signature": "84584da301276761646472657373581d60a64aa1009d0f106fd742a79ee68bd9a5fd815ffa587d6d0aa68cb51e045820f84f04c0054dbbb0a7fcbd1584dac460cbd1b14723a6e9d2571477ba21644858a166686173686564f45818417468656e61204d495552207c2031363638323538353834584020bd7dfdf5d6759193e5a63004949bbb116b702f5e6a334394b55937921bc060e762d7101b1e7200aa53cd6c0e2e373842eb79d20bff063e7c03630d66665a03",
        },
    )

    assert response.status_code == 400

    assert "success" in response.json
    assert response.json["success"] is False

    # Create user
    user = User(
        email="hanz@email.com",
        stake_address="stake_test1uzny4ggqn583qm7hg2neae5tmxjlmq2llfv86mg256xt28sv20c2r",
        payment_address="addr_test123",
    )

    with app.app_context():
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)

    print(User.query.all())

    # Signature is not valid
    response = client.post(
        "/projects/create",
        json={
            "name": "Project",
            "creator": "stake_test1uzny4ggqn583qm7hg2neae5tmxjlmq2llfv86mg256xt28sv20c2r",
            "short_description": "lorem ipsum...",
            "long_description": "lorem ipsum dolor sit amet...",
            "subjects": ["Math", "Tourism"],
            "days_to_complete": 15,
            "deliverables": ["I'm gonna do real good", "Trust me bro"],
            "mediators": [
                "stake_test1uzny4ggqn583qm7hg2neae5tmxjlmq2llfv86mg256xt28sv20c2r"
            ],
            "signature": "84584da301276761646472657373581d60f30fcc4e977c7afeb89eefefe327a4d7e71e8767277f275421541320045820db35a31336847bec6a8e5b78b05e14575e7700308bd37302864360b057bcbc54a166686173686564f45818417468656e61204d495552207c203136363832353835383458407b41326e9dc19ea5aa4c49a20cd5828f6f57e13adb4b7eab89a8a0d3cad74009ab6312fae81152d68dcbafed7758524f02e25994f469aff5bec4ebc1c658930d",
        },
    )

    assert response.status_code == 400

    assert "success" in response.json
    assert response.json["success"] is False

    # Creator does exist
    response = client.post(
        "/projects/create",
        json={
            "name": "Project",
            "creator": "stake_test1uzny4ggqn583qm7hg2neae5tmxjlmq2llfv86mg256xt28sv20c2r",
            "short_description": "lorem ipsum...",
            "long_description": "lorem ipsum dolor sit amet...",
            "subjects": ["Math", "Tourism"],
            "days_to_complete": 15,
            "deliverables": ["I'm gonna do real good", "Trust me bro"],
            "mediators": [
                "stake_test1uzny4ggqn583qm7hg2neae5tmxjlmq2llfv86mg256xt28sv20c2r"
            ],
            "signature": "84584da301276761646472657373581d60a64aa1009d0f106fd742a79ee68bd9a5fd815ffa587d6d0aa68cb51e045820f84f04c0054dbbb0a7fcbd1584dac460cbd1b14723a6e9d2571477ba21644858a166686173686564f45818417468656e61204d495552207c2031363638323538353834584020bd7dfdf5d6759193e5a63004949bbb116b702f5e6a334394b55937921bc060e762d7101b1e7200aa53cd6c0e2e373842eb79d20bff063e7c03630d66665a03",
        },
    )

    assert response.status_code == 200
    assert response.json == {"success": True}

    projects = Project.query.all()
    assert len(projects) == 1

    # Make sure project created is equal to the sample provided
    project: Project = projects[0]
    assert project.name == "Project"

    assert (
        project.creator.stake_address
        == "stake_test1uzny4ggqn583qm7hg2neae5tmxjlmq2llfv86mg256xt28sv20c2r"
    )

    assert project.short_description == "lorem ipsum..."
    assert project.long_description == "lorem ipsum dolor sit amet..."

    assert set([subject.subject_name for subject in project.subjects]) == {
        "Math",
        "Tourism",
    }

    assert project.days_to_complete == 15

    assert set([mediator.email for mediator in project.mediators]) == {"hanz@email.com"}

    assert set([deliverable.deliverable for deliverable in project.deliverables]) == {
        "I'm gonna do real good",
        "Trust me bro",
    }


def test_get_project(api):
    client, app = api

    sys.path.append("src")

    from model import db, Project, User, Subject, Deliverable

    user_1 = User(
        email="alice@email.com",
        stake_address="stake_test123",
        payment_address="addr_test123",
    )

    user_2 = User(
        email="bob@email.com",
        stake_address="stake_test456",
        payment_address="addr_test456",
    )

    subject_1 = Subject()
    subject_1.subject_name = "Math"

    subject_2 = Subject()
    subject_2.subject_name = "Tourism"

    deliverable_1 = Deliverable()
    deliverable_1.deliverable = "I am going to do it"

    deliverable_2 = Deliverable()
    deliverable_2.deliverable = "I am doint it I swear"

    project_1 = Project()
    project_1.project_identifier = "id"
    project_1.creator = user_1
    project_1.subjects = [subject_1, subject_2]

    project_1.name = "Project"

    project_1.short_description = "lorem ipsum..."
    project_1.long_description = "lorem ipsum dolor sit amet..."

    project_1.days_to_complete = 15

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

    response = client.get("/projects/id")

    assert response.status_code == 200
    assert response.json == {
        "success": True,
        "project": {
            "project_id": "id",
            "name": "Project",
            "creator": {
                "email": "alice@email.com",
                "stake_address": "stake_test123",
                "payment_address": "addr_test123",
            },
            "funders": [],
            "total_funding_amount": 0,
            "short_description": "lorem ipsum...",
            "long_description": "lorem ipsum dolor sit amet...",
            "subjects": ["Math", "Tourism"],
            "days_to_complete": 15,
            "deliverables": ["I am going to do it", "I am doint it I swear"],
            "mediators": [
                {
                    "stake_address": "stake_test123",
                    "payment_address": "addr_test123",
                    "email": "alice@email.com",
                },
                {
                    "stake_address": "stake_test456",
                    "payment_address": "addr_test456",
                    "email": "bob@email.com",
                },
            ],
        },
    }


def test_get_project_user(api):
    client, app = api

    sys.path.append("src")

    from model import db, Project, User, Subject, Deliverable, Funding

    project = Project()
    project.project_identifier = "project_id"
    project.creator = User(
        email="alice@email.com",
        stake_address="stake_test123",
        payment_address="addr_test123",
    )
    project.subjects = [Subject(subject_name="Math"), Subject(subject_name="Tourism")]

    project.name = "Project"

    project.short_description = "lorem ipsum..."
    project.long_description = "lorem ipsum dolor sit amet..."

    project.days_to_complete = 15

    project.deliverables = [
        Deliverable(deliverable="I am going to do it"),
        Deliverable(deliverable="I am doint it I swear"),
    ]
    project.mediators = [
        User(
            email="bob@email.com",
            stake_address="stake_test456",
            payment_address="addr_test456",
        )
    ]

    project.creation_date = datetime.datetime(2022, 6, 24, 12, 0, 0)

    with app.app_context():
        db.session.add(project)
        db.session.commit()
        db.session.refresh(project)

    funding = Funding(
        funder=User(
            email="charlie@email.com",
            stake_address="stake_test789",
            payment_address="addr_test789",
        ),
        project=project,
        status="submitted",
        transaction_hash="hash",
        transaction_index=0,
        amount=10_000_000,
    )

    with app.app_context():
        db.session.add(funding)
        db.session.commit()

    response = client.get(f"/projects/project_id/stake_test123")

    print(response.json)
    assert response.status_code == 200
    assert response.json == {
        "funder": False,
        "creator": True,
        "mediator": False,
    }

    response = client.get(f"/projects/project_id/stake_test456")

    print(response.json)
    assert response.status_code == 200
    assert response.json == {
        "funder": False,
        "creator": False,
        "mediator": True,
    }

    response = client.get(f"/projects/project_id/stake_test789")

    print(response.json)
    assert response.status_code == 200
    assert response.json == {
        "funder": True,
        "creator": False,
        "mediator": False,
    }


def test_submit_project(api, monkeypatch):
    client, app = api

    sys.path.append("src")

    monkeypatch.setattr("api.projects.auth_tools.user_can_signin", lambda *_: True)

    from model import db, Project, User, Subject, Deliverable, Submission

    alice = User(
        email="alice@email.com",
        stake_address="stake_test123",
        payment_address="addr_test123",
    )

    bob = User(
        email="bob@email.com",
        stake_address="stake_test456",
        payment_address="addr_test456",
    )

    charlie = User(
        email="charlie@email.com",
        stake_address="stake_test789",
        payment_address="addr_test789",
    )

    project = Project(
        project_identifier="project_id",
        creator=alice,
        subjects=[Subject(subject_name="Math"), Subject(subject_name="Tourism")],
        name="Project",
        short_description="lorem ipsum...",
        long_description="lorem ipsum dolor sit amet...",
        days_to_complete=15,
        deliverables=[
            Deliverable(deliverable="I am going to do it"),
            Deliverable(deliverable="I am doint it I swear"),
        ],
        mediators=[bob],
        status="review",
        creation_date=datetime.datetime(2022, 6, 24, 12, 0, 0),
        disqualified=True
    )

    with app.app_context():
        db.session.add(alice)
        db.session.add(bob)
        db.session.add(charlie)
        db.session.add(project)

        db.session.commit()

        db.session.refresh(alice)
        db.session.refresh(bob)
        db.session.refresh(charlie)
        db.session.refresh(project)

    # Should not be able to do submissions if project is disqualified

    response = client.post(
        "/projects/submit/project_id",
        json={
            "title": "Very Nice Title",
            "content": "It is thereby proven that Nicholas Cage is a vampire",
            "signature": "<signature>",
        },
    )

    print(response.json)

    assert response.status_code == 400

    project.disqualified = False

    with app.app_context():
        db.session.add(project)
        db.session.commit()

    response = client.post(
        "/projects/submit/project_id",
        json={
            "title": "Very Nice Title",
            "content": "It is thereby proven that Nicholas Cage is a vampire",
            "signature": "<signature>",
        },
    )

    print(response.json)

    assert response.status_code == 200
    assert response.json == {"success": True}

    with app.app_context():
        project = Project.query.filter(
            Project.project_identifier == "project_id"
        ).first()

        assert len(project.submissions) == 1

        submission = project.submissions[0]

        assert submission.title == "Very Nice Title"
        assert (
            submission.content == "It is thereby proven that Nicholas Cage is a vampire"
        )


def test_submit_review(api, monkeypatch):
    client, app = api

    sys.path.append("src")

    monkeypatch.setattr("api.projects.auth_tools.user_can_signin", lambda *_: True)

    from model import db, Project, User, Subject, Deliverable, Submission, Review

    alice = User(
        email="alice@email.com",
        stake_address="stake_test123",
        payment_address="addr_test123",
    )

    bob = User(
        email="bob@email.com",
        stake_address="stake_test456",
        payment_address="addr_test456",
    )

    charlie = User(
        email="charlie@email.com",
        stake_address="stake_test789",
        payment_address="addr_test789",
    )

    project = Project(
        project_identifier="project_id",
        creator=alice,
        subjects=[Subject(subject_name="Math"), Subject(subject_name="Tourism")],
        name="Project",
        short_description="lorem ipsum...",
        long_description="lorem ipsum dolor sit amet...",
        days_to_complete=15,
        deliverables=[
            Deliverable(deliverable="I am going to do it"),
            Deliverable(deliverable="I am doint it I swear"),
        ],
        mediators=[bob],
        creation_date=datetime.datetime(2022, 6, 24, 12, 0, 0),
    )

    submission = Submission(
        submission_identifier="submission_id",
        project=project,
        title="Title",
        content="content",
    )

    with app.app_context():
        db.session.add(alice)
        db.session.add(bob)
        db.session.add(charlie)
        db.session.add(project)
        db.session.add(submission)

        db.session.commit()

        db.session.refresh(alice)
        db.session.refresh(bob)
        db.session.refresh(charlie)
        db.session.refresh(project)
        db.session.refresh(submission)

    # Try with reviewer who is not the mediator (should not be allowed)

    response = client.post(
        "/projects/review/submission_id",
        json={
            "reviewer": "stake_test789",
            "approval": True,
            "disqualified": False,
            "review": "I approve this project",
            "deadline": 1_704_067_200,  # 2024-01-01 00:00:00 GMT
            "signature": "<signature>",
        },
    )

    print(response.json)

    assert response.status_code == 400

    response = client.post(
        "/projects/review/submission_id",
        json={
            "reviewer": "stake_test456",
            "approval": True,
            "disqualified": False,
            "review": "I approve this project",
            "deadline": 1_704_067_200,  # 2024-01-01 00:00:00 GMT
            "signature": "<signature>",
        },
    )

    print(response.json)

    assert response.status_code == 200
    assert response.json == {"success": True}

    with app.app_context():
        reviews = Review.query.all()

        assert len(reviews) == 1

        review = reviews[0]

        assert review.submission_id == submission.id
        assert review.reviewer_id == bob.id

        assert review.approval == True
        assert review.review == "I approve this project"
        assert review.deadline == datetime.datetime(2024, 1, 1, 0, 0)

    # Should not be able to review the same submission twice
    response = client.post(
        "/projects/review/submission_id",
        json={
            "reviewer": "stake_test456",
            "approval": True,
            "disqualified": False,
            "review": "I approve this project",
            "deadline": 1_704_067_200,  # 2024-01-01 00:00:00 GMT
            "signature": "<signature>",
        },
    )

    print(response.json)

    assert response.status_code == 400

    # If disqualified, should update project accordingly

    submission_2 = Submission(
        submission_identifier="submission_id_2",
        project=project,
        title="Title 2",
        content="content 2",
    )

    with app.app_context():
        db.session.add(submission_2)

        db.session.commit()

        db.session.refresh(submission_2)

    response = client.post(
        "/projects/review/submission_id_2",
        json={
            "reviewer": "stake_test456",
            "approval": False,
            "disqualified": True,
            "review": "I hate this project",
            "deadline": 1_704_067_200,  # 2024-01-01 00:00:00 GMT
            "signature": "<signature>",
        },
    )

    print(response.json)

    assert response.status_code == 200
    
    with app.app_context():
        projects = Project.query.all()

        assert len(projects) == 1

        project = projects[0]
        assert project.disqualified == True


def test_get_submissions(api):
    client, app = api

    sys.path.append("src")

    from model import db, Project, User, Subject, Deliverable, Submission, Review

    alice = User(
        email="alice@email.com",
        stake_address="stake_test123",
        payment_address="addr_test123",
    )

    bob = User(
        email="bob@email.com",
        stake_address="stake_test456",
        payment_address="addr_test456",
    )

    charlie = User(
        email="charlie@email.com",
        stake_address="stake_test789",
        payment_address="addr_test789",
    )

    project = Project(
        project_identifier="project_id",
        creator=alice,
        subjects=[Subject(subject_name="Math"), Subject(subject_name="Tourism")],
        name="Project",
        short_description="lorem ipsum...",
        long_description="lorem ipsum dolor sit amet...",
        days_to_complete=15,
        deliverables=[
            Deliverable(deliverable="I am going to do it"),
            Deliverable(deliverable="I am doint it I swear"),
        ],
        mediators=[bob],
        creation_date=datetime.datetime(2022, 6, 24, 12, 0, 0),
    )

    with app.app_context():
        db.session.add(project)

        expected_submissions = []
        for i in range(10):
            submission = Submission(
                submission_identifier=f"submission_id_{i}",
                project=project,
                title=f"Title_{i}",
                content=f"content_{i}",
            )

            review = Review(
                review_identifier=f"review_id_{i}",
                submission=submission,
                reviewer=charlie,
                approval=True,
                review=f"Impressive work {i}",
                deadline=datetime.datetime(2024, 1, 1, 0, 0),
            )

            db.session.add(submission)
            db.session.add(review)

            expected_submissions.append(
                {
                    "submission_id": f"submission_id_{i}",
                    "project_id": "project_id",
                    "title": f"Title_{i}",
                    "content": f"content_{i}",
                    "review": {
                        "review_id": f"review_id_{i}",
                        "submission_id": f"submission_id_{i}",
                        "reviewer": {
                            "email": "charlie@email.com",
                            "payment_address": "addr_test789",
                            "stake_address": "stake_test789",
                        },
                        "approval": True,
                        "review": f"Impressive work {i}",
                        "deadline": 1_704_067_200,  # 2024-01-01 00:00:00 GMT
                    },
                }
            )

        db.session.commit()

    response = client.get("/submissions/project_id")

    assert response.status_code == 200
    assert response.json == {
        "count": 10,
        "submissions": expected_submissions,
        "mediators": [
            {
                "email": "bob@email.com",
                "payment_address": "addr_test456",
                "stake_address": "stake_test456",
            }
        ],
        "submitter": {
            "email": "alice@email.com",
            "payment_address": "addr_test123",
            "stake_address": "stake_test123",
        },
    }


def test_add_mediator(api, monkeypatch):
    client, app = api

    sys.path.append("src")

    monkeypatch.setattr("api.projects.os.environ", {"API_KEY": "password"})

    from model import db, Project, User, Subject, Deliverable

    alice = User(
        id=0,
        email="alice@email.com",
        stake_address="stake_test123",
        payment_address="addr_test123",
    )

    bob = User(
        id=1,
        email="bob@email.com",
        stake_address="stake_test456",
        payment_address="addr_test456",
    )

    charlie = User(
        id=2,
        email="charlie@email.com",
        stake_address="stake_test789",
        payment_address="addr_test789",
    )

    project = Project(
        project_identifier="project_id",
        creator=alice,
        subjects=[Subject(subject_name="Math"), Subject(subject_name="Tourism")],
        name="Project",
        short_description="lorem ipsum...",
        long_description="lorem ipsum dolor sit amet...",
        days_to_complete=15,
        deliverables=[
            Deliverable(deliverable="I am going to do it"),
            Deliverable(deliverable="I am doint it I swear"),
        ],
        mediators=[bob],
        creation_date=datetime.datetime(2022, 6, 24, 12, 0, 0),
    )

    with app.app_context():
        db.session.add(project)
        db.session.add(charlie)
        db.session.commit()

    # Try different api key

    response = client.post(
        "/projects/mediators/add/project_id",
        json={"mediator_stake_address": "stake_test789", "api_key": "wrong_password"},
    )

    assert response.status_code == 400

    response = client.post(
        "/projects/mediators/add/project_id",
        json={"mediator_stake_address": "stake_test789", "api_key": "password"},
    )

    print(response.json)

    assert response.status_code == 200
    assert response.json == {"success": True}

    with app.app_context():
        projects = Project.query.all()

        assert len(projects) == 1

        project = projects[0]

        assert [mediator.id for mediator in project.mediators] == [1, 2]
