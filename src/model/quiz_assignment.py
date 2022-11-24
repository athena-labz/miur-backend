from . import db

from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, func, and_

from typing import List

from .quiz import Quiz
from .user import User

import datetime
import uuid


class QuizAssignment(db.Model):
    __tablename__ = "quiz_assignment"

    id = db.Column(db.Integer, primary_key=True)
    quiz_assignmenr_identifier = db.Column(
        db.String(64), default=lambda: str(uuid.uuid4()), nullable=False
    )

    assignee_id = db.Column(db.Integer, ForeignKey("user.id"), nullable=False)
    assignee = relationship("User", back_populates="quiz_assignments")

    quiz_id = db.Column(db.Integer, ForeignKey("quiz.id"), nullable=False)
    quiz = relationship("Quiz", back_populates="assignments")

    powerups = relationship("PowerUp", back_populates="quiz_assignment")

    # None means this assignment has ended
    current_question = db.Column(db.Integer, default=0)
    remaining_attempts = db.Column(db.Integer, default=3, nullable=False)

    # None means it's still in progress
    completed_success = db.Column(db.Boolean)

    creation_date = db.Column(
        db.DateTime(timezone=False), server_default=func.now(), nullable=False
    )

    def info(self):
        return {
            "quiz_id": self.quiz.quiz_identifier,
            "assignee_stake_address": self.assignee.stake_address,
            "powerups": [powerup.info() for powerup in self.powerups],
            "current_question": self.current_question,
            "remaining_attempts": self.remaining_attempts,
            "completed_success": self.completed_success,
            "creation_date": self.creation_date.strftime("%Y/%m/%d %H:%M:%S"),
        }

    @staticmethod
    def find(quiz_id: str, assignee_stake_address: str):
        quiz = Quiz.find(quiz_id)
        if quiz is None:
            return None

        user = User.find(assignee_stake_address)
        if user is None:
            return None

        return QuizAssignment.query.filter(
            and_(
                QuizAssignment.quiz_id == quiz.id, QuizAssignment.assignee_id == user.id
            )
        ).first()

    @staticmethod
    def create(quiz_id: str, assignee_stake_address: str):
        quiz = Quiz.find(quiz_id)
        if quiz is None:
            raise ValueError(
                f"Trying to create QuizAssignment with quiz that does not exist {quiz_id}"
            )

        user = User.find(assignee_stake_address)
        if user is None:
            raise ValueError(
                f"Trying to create QuizAssignment with assignee that does not exist {assignee_stake_address}"
            )

        return QuizAssignment(quiz=quiz, assignee=user)

    @staticmethod
    def find_or_create(quiz_id: str, assignee_stake_address: str):
        quiz_assignment: QuizAssignment | None = QuizAssignment.find(
            quiz_id, assignee_stake_address
        )

        if quiz_assignment is None:
            quiz_assignment = QuizAssignment.create(quiz_id, assignee_stake_address)

            db.session.add(quiz_assignment)
            db.session.commit()

        return quiz_assignment

    @staticmethod
    def sample(
        assignee: User = -1,
        quiz: Quiz = -1,
        powerups: list = -1,
        current_question: int = -1,
        remaining_attempts: int = -1,
        completed_success: bool = -1,
        creation_date: datetime.datetime = -1,
    ):
        def if_else(if_val, else_val):
            return if_val if if_val != -1 else else_val

        return QuizAssignment(
            assignee=if_else(assignee, User.sample()),
            quiz=if_else(quiz, Quiz.sample()),
            powerups=if_else(powerups, []),
            current_question=if_else(current_question, 0),
            remaining_attempts=if_else(remaining_attempts, 3),
            completed_success=if_else(completed_success, None),
            creation_date=if_else(creation_date, datetime.datetime.utcnow()),
        )
