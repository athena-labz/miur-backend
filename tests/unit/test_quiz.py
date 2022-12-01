from fixtures import api

import datetime


def test_create_quiz(api):
    client, app = api

    from model import Quiz, User, db

    with app.app_context():
        alice = User.sample()

        db.session.add(alice)
        db.session.commit()
        db.session.refresh(alice)

    res = client.post(
        "/quiz/create",
        json={
            "creator_name": "Alice",
            "creator_stake_address": alice.stake_address,
            "questions": [
                {
                    "question": "What is the capital of Brazil?",
                    "answers": ["Brasilia", "Rio de Janeiro"],
                    "hints": ["Think about it's name"],
                    "right_answer": 0,
                }
            ],
        },
    )

    assert res.status_code == 200

    quizes = Quiz.query.all()
    assert len(quizes) == 1

    quiz: Quiz = quizes[0]
    assert quiz.creator_name == "Alice"
    assert quiz.creator_id == alice.id
    assert quiz.questions == {
        "questions": [
            {
                "question": "What is the capital of Brazil?",
                "answers": ["Brasilia", "Rio de Janeiro"],
                "hints": ["Think about it's name"],
                "right_answer": 0,
            }
        ]
    }


def test_assign_quiz(api):
    client, app = api

    from model import Quiz, User, db

    questions = [
        {
            "question": "What is the capital of Brazil?",
            "answers": ["Brasilia", "Rio de Janeiro"],
            "hints": ["Think about it's name"],
            "right_answer": 0,
        }
    ]

    with app.app_context():
        user = User.sample()
        quiz = Quiz.sample()

        db.session.add(user)
        db.session.add(quiz)
        db.session.commit()

        db.session.refresh(user)
        db.session.refresh(quiz)

    res = client.post(
        f"/quiz/assign",
        json={
            "quiz_id": quiz.quiz_identifier,
            "user_stake_address": user.stake_address,
        },
    )

    assert res.status_code == 200


def test_get_quiz(api, monkeypatch):
    client, app = api

    from model import Quiz, User, db

    questions = [
        {
            "question": "What is the capital of Brazil?",
            "answers": ["Brasilia", "Rio de Janeiro"],
            "hints": ["Think about it's name"],
            "right_answer": 0,
        }
    ]

    with app.app_context():
        alice = User.sample(stake_address="stake_test123")
        quiz = Quiz.sample(
            quiz_identifier="quiz_id",
            creator=alice,
            creator_name="Alice",
            questions=questions,
            creation_date=datetime.datetime(2012, 12, 12, 12, 12, 12),
        )

        db.session.add(alice)
        db.session.add(quiz)
        db.session.commit()

        db.session.refresh(alice)
        db.session.refresh(quiz)

    res = client.get(f"/quiz/{quiz.quiz_identifier}")

    assert res.status_code == 200
    assert res.json == {
        "quiz_id": "quiz_id",
        "creator_name": "Alice",
        "creator_stake_address": "stake_test123",
        "questions": [
            {
                "question": "What is the capital of Brazil?",
                "answers": ["Brasilia", "Rio de Janeiro"],
            }
        ],
        "creation_date": "2012/12/12 12:12:12",
    }


def test_attempt_answer(api):
    pass


def test_use_powerup(api):
    pass
