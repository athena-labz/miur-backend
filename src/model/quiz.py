from . import db

from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from typing import List

from .user import User

import uuid
import json

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

    creator_name = db.Column(db.String(), nullable=False)

    questions = db.Column(db.JSON, nullable=False)

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
    def sample(
        creator: User = -1,
        assignments: List[str] = -1,
        creator_name: str = -1,
        questions: dict = -1,
    ):
        def if_else(if_val, else_val):
            return if_val if if_val != -1 else else_val

        return Quiz(
            creator=if_else(creator, None),
            assignments=if_else(assignments, []),
            creator_name=if_else(creator_name, "Alice"),
            questions=if_else(
                questions,
                {
                    "questions": [
                        Quiz.create_question(
                            f"Question #{i+1}",
                            [f"Answer #{j+1}" for j in range(5)],
                            [f"Hint #{j+1}" for j in range(3)],
                            0,
                        )
                        for i in range(10)
                    ]
                },
            ),
        )
