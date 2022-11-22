from fixtures import api


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
