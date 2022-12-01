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


def test_get_quiz_assignement(api):
    # Should return information about the quiz assignment,
    # such as stake address from the user who is attempting it,
    # quiz identifier, number of lifes, available powerups and
    # quiz assignment status

    client, app = api

    from model import QuizAssignment, db

    quiz_assignment = QuizAssignment.sample()
    with app.app_context():
        db.session.add(quiz_assignment)
        db.session.commit()

        res = client.get(
            f"/quiz/assignment/{quiz_assignment.quiz.quiz_identifier}/{quiz_assignment.assignee.stake_address}"
        )

        assert res.status_code == 200
        assert res.json == quiz_assignment.info()


def test_attempt_answer(api, monkeypatch):
    # Should be a POST request that requires stake address authentication
    # If user get's right answer, should advance to next question or
    # complete it if it's the last item
    # Otherwise, should either lose a life or lose the whole game if the
    # lives are over

    client, app = api

    monkeypatch.setattr("lib.auth_tools.validate_signature", lambda *_: True)

    from model import Quiz, QuizAssignment, db

    questions = [
        {
            "question": "What is the capital of Brazil?",
            "answers": ["Brasilia", "Rio de Janeiro"],
            "hints": ["Think about it's name"],
            "right_answer": 0,
        },
        {
            "question": "Am I gonna give you up?",
            "answers": ["Yes", "No", "Never"],
            "hints": ["Am I gonna let you down?"],
            "right_answer": 2,
        },
        {
            "question": "Who invented the light?",
            "answers": ["Thomas Eddison", "Nikola Tesla", "God"],
            "hints": [],
            "right_answer": 2,
        },
    ]

    quiz_assignment = QuizAssignment.sample(
        quiz=Quiz.sample(questions=questions), remaining_attempts=3
    )
    with app.app_context():
        db.session.add(quiz_assignment)
        db.session.commit()

        res = client.post(
            f"/quiz/attempt/{quiz_assignment.quiz.quiz_identifier}",
            json={
                "stake_address": quiz_assignment.assignee.stake_address,
                "answer": 0,
                "signature": "sample_signature",
            },
        )

        assert res.status_code == 200
        assert res.json == {
            "right_answer": True,
            "state": "ongoing",
            "remaining_attempts": 3,
            "current_question": 1
        }

        res = client.post(
            f"/quiz/attempt/{quiz_assignment.quiz.quiz_identifier}",
            json={
                "stake_address": quiz_assignment.assignee.stake_address,
                "answer": 0, # Wrong answer
                "signature": "sample_signature",
            },
        )

        assert res.status_code == 200
        assert res.json == {
            "right_answer": False,
            "state": "ongoing",
            "remaining_attempts": 2,
            "current_question": 1
        }

        res = client.post(
            f"/quiz/attempt/{quiz_assignment.quiz.quiz_identifier}",
            json={
                "stake_address": quiz_assignment.assignee.stake_address,
                "answer": 2,
                "signature": "sample_signature",
            },
        )

        assert res.status_code == 200
        assert res.json == {
            "right_answer": True,
            "state": "ongoing",
            "remaining_attempts": 2,
            "current_question": 2
        }

        res = client.post(
            f"/quiz/attempt/{quiz_assignment.quiz.quiz_identifier}",
            json={
                "stake_address": quiz_assignment.assignee.stake_address,
                "answer": 2,
                "signature": "sample_signature",
            },
        )

        assert res.status_code == 200
        assert res.json == {
            "right_answer": True,
            "state": "completed_success",
            "remaining_attempts": 2,
        }

        quiz_assignment_2 = QuizAssignment.sample(
            quiz=Quiz.sample(questions=questions[:1]), remaining_attempts=3
        )

        db.session.add(quiz_assignment_2)
        db.session.commit()

        for i in range(1, 3):
            res = client.post(
                f"/quiz/attempt/{quiz_assignment_2.quiz.quiz_identifier}",
                json={
                    "stake_address": quiz_assignment_2.assignee.stake_address,
                    "answer": 1, # Wrong answer
                    "signature": "sample_signature",
                },
            )

            assert res.status_code == 200
            assert res.json == {
                "right_answer": False,
                "state": "ongoing",
                "remaining_attempts": 3-i,
                "current_question": 0
            }

        res = client.post(
            f"/quiz/attempt/{quiz_assignment_2.quiz.quiz_identifier}",
            json={
                "stake_address": quiz_assignment_2.assignee.stake_address,
                "answer": 1, # Wrong answer
                "signature": "sample_signature",
            },
        )

        assert res.status_code == 200
        assert res.json == {
            "right_answer": False,
            "state": "completed_failure",
            "remaining_attempts": 0,
        }


def test_use_powerup(api):
    pass