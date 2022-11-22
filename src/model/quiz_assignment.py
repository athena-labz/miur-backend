from . import db

from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, func

from typing import List

from .quiz import Quiz
from .user import User

import datetime


class QuizAssignment(db.Model):
    __tablename__ = "quiz_assignment"

    id = db.Column(db.Integer, primary_key=True)

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

    
    @staticmethod
    def sample(
        assignee: User = -1,
        quiz: Quiz = -1,
        powerups: list = -1,
        current_question: int = -1,
        remaining_attempts: int = -1,
        completed_success: bool = -1,
        creation_date: datetime.datetime = -1
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
