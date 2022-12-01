from __future__ import annotations

from model import Quiz, QuizAssignment, User, db
from lib import auth_tools
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
            questions={"questions": data["questions"]},
        )

    db.session.add(quiz)
    db.session.commit()

    return {"success": True}, 200


def assign_quiz():
    data = request.json

    quiz_id = data["quiz_id"]
    user_stake_address = data["user_stake_address"]

    quiz_assignment = QuizAssignment.find_or_create(quiz_id, user_stake_address)

    return quiz_assignment.info()


def get_quiz(quiz_id: str):
    quiz: Quiz | None = Quiz.find(quiz_id)
    if quiz is None:
        return {"message": f"Quiz {quiz_id} not found"}, 404

    return quiz.public_info(), 200


def get_assignment(quiz_id: str, stake_address: str):
    quiz: Quiz = Quiz.find(quiz_id)
    if quiz is None:
        return {
            "message": f"Quiz {quiz_id} does not exist",
            "code": "quiz-not-found",
        }, 404

    user: User = User.find(stake_address)
    if user is None:
        return {
            "message": f"User {stake_address} does not exist",
            "code": "user-not-found",
        }, 404

    quiz_assignment: QuizAssignment = QuizAssignment.query.filter(
        (QuizAssignment.quiz_id == quiz.id) & (QuizAssignment.assignee_id == user.id)
    ).first()

    if quiz_assignment is None:
        return {
            "message": f"Quiz Assignment for quiz {quiz_id} and user {stake_address} does not exist",
            "code": "quiz-assignment-not-found",
        }, 404

    return quiz_assignment.info(), 200


def attempt_answer(quiz_id: str):
    data = request.json

    stake_address = data["stake_address"]
    answer = data["answer"]
    signature = data["signature"]

    quiz: Quiz = Quiz.find(quiz_id)
    if quiz is None:
        return {
            "message": f"Quiz {quiz_id} does not exist",
            "code": "quiz-not-found",
        }, 404

    user: User = User.find(stake_address)
    if user is None:
        return {
            "message": f"User {stake_address} does not exist",
            "code": "user-not-found",
        }, 404

    quiz_assignment: QuizAssignment = QuizAssignment.query.filter(
        (QuizAssignment.quiz_id == quiz.id) & (QuizAssignment.assignee_id == user.id)
    ).first()

    if quiz_assignment is None:
        return {
            "message": f"Quiz Assignment for quiz {quiz_id} and user {stake_address} does not exist",
            "code": "quiz-assignment-not-found",
        }, 404

    if not auth_tools.validate_signature(signature, stake_address):
        return {
            "success": False,
            "message": "Invalid signature",
            "code": "invalid-signature",
        }, 400

    current_question = quiz.questions[quiz_assignment.current_question]

    if answer == current_question["right_answer"]:
        # Right answer scenario

        response = {
            "right_answer": True,
            "remaining_attempts": quiz_assignment.remaining_attempts,
        }

        if quiz_assignment.current_question == len(quiz.questions) - 1:
            # If this was the last question

            quiz_assignment.complete_with_success()
            response["state"] = "completed_success"
        else:
            quiz_assignment.move_next_question()

            response["state"] = "ongoing"
            response["current_question"] = quiz_assignment.current_question

        return response, 200
    else:
        # Wrong answer scenario

        response = {
            "right_answer": False,
            "remaining_attempts": quiz_assignment.remaining_attempts - 1,
        }

        if quiz_assignment.remaining_attempts == 1:
            # If this was the last attempt

            quiz_assignment.complete_with_failure()
            response["state"] = "completed_failure"
        else:
            quiz_assignment.lose_attempt()

            response["state"] = "ongoing"
            response["current_question"] = quiz_assignment.current_question

        return response, 200
