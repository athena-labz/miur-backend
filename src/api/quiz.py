from model import Quiz, User, db
from flask import request


def create_quiz():
    data = request.json

    creator = None
    if "creator_stake_address" in data:
        creator = User.query.filter(
            User.stake_address == data["creator_stake_address"]
        ).first()

    with db.session.no_autoflush:
        quiz = Quiz(
            creator=creator,
            creator_name=data["creator_name"],
            questions={"questions": data["questions"]}
        )

    db.session.add(quiz)
    db.session.commit()

    return {"success": True}, 200
