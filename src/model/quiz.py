from . import db

from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, func
from typing import List

from .user import User

import datetime
import uuid

sample_questions = {
    "questions": [
        {
            "question": "...",
            "answers": ["...", "..."],
            "hints": ["..."],
            "right_answer": 0,
        }
    ]
}


class Quiz(db.Model):
    __tablename__ = "quiz"

    id = db.Column(db.Integer, primary_key=True)
    quiz_identifier = db.Column(
        db.String(64), default=lambda: str(uuid.uuid4()), nullable=False
    )

    creator_id = db.Column(db.Integer, ForeignKey("user.id"))
    creator = relationship("User", back_populates="created_quizes")

    assignments = relationship("QuizAssignment", back_populates="quiz")
    answer_attempts = relationship("AttemptAnswer", back_populates="quiz")

    creator_name = db.Column(db.String(), nullable=False)

    questions = db.Column(db.JSON, nullable=False)

    creation_date = db.Column(
        db.DateTime(timezone=False), server_default=func.now(), nullable=False
    )

    def info(self):
        return {
            "quiz_id": self.quiz_identifier,
            "creator_name": self.creator_name,
            "creator_stake_address": self.creator.stake_address
            if self.creator
            else None,
            "questions": self.questions,
            "creation_date": self.creation_date.strftime("%Y/%m/%d %H:%M:%S"),
        }

    def public_info(self):
        return {
            "quiz_id": self.quiz_identifier,
            "creator_name": self.creator_name,
            "creator_stake_address": self.creator.stake_address
            if self.creator
            else None,
            "questions": [
                Quiz.public_question(question) for question in self.questions
            ],
            "creation_date": self.creation_date.strftime("%Y/%m/%d %H:%M:%S"),
        }

    @staticmethod
    def find(quiz_id: str):
        return Quiz.query.filter(Quiz.quiz_identifier == quiz_id).first()

    @staticmethod
    def created_by_user(user: User):
        return Quiz.query.filter(Quiz.creator_id == user.id).all()

    @staticmethod
    def create_question(
        question: str, answers: List[str], hints: List[str], right_answer: int
    ) -> dict:
        return {
            "question": question,
            "answers": answers,
            "hints": hints,
            "right_answer": right_answer,
        }

    @staticmethod
    def public_question(question: dict) -> dict:
        return {
            "question": question["question"],
            "answers": question["answers"],
        }

    @staticmethod
    def sample(
        quiz_identifier: str = -1,
        creator: User = -1,
        assignments: List[str] = -1,
        creator_name: str = -1,
        questions: dict = -1,
        creation_date: datetime.datetime = -1,
    ):
        def if_else(if_val, else_val):
            return if_val if if_val != -1 else else_val

        return Quiz(
            quiz_identifier=if_else(quiz_identifier, str(uuid.uuid4())),
            creator=if_else(creator, None),
            assignments=if_else(assignments, []),
            creator_name=if_else(creator_name, "Alice"),
            questions=if_else(
                questions,
                [
                    Quiz.create_question(
                        f"Question #{i+1}",
                        [f"Answer #{j+1}" for j in range(5)],
                        [f"Hint #{j+1}" for j in range(3)],
                        0,
                    )
                    for i in range(10)
                ],
            ),
            creation_date=if_else(creation_date, datetime.datetime.utcnow()),
        )
