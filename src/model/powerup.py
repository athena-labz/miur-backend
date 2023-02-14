from . import db

from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, func
from typing import List, Callable, Dict

from .quiz_assignment import QuizAssignment

import random


class PowerUp(db.Model):
    __tablename__ = "powerup"

    id = db.Column(db.Integer, primary_key=True)

    quiz_assignment_id = db.Column(
        db.Integer, ForeignKey("quiz_assignment.id"), nullable=False
    )
    quiz_assignment = relationship("QuizAssignment", back_populates="powerups")

    name = db.Column(db.String, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)

    def info(self):
        return {
            "name": self.name,
            "used": self.used,
        }

    def get_hints(self, question_index: int) -> str:
        random.seed(self.id)

        return random.choice(
            self.quiz_assignment.quiz.questions[question_index]["hints"]
        )

    def get_percentages(self, question_index: int) -> str:
        random.seed(self.id)

        return random.choice(
            self.quiz_assignment.quiz.questions[question_index]["hints"]
        )

    # def powerups_map(self) -> Dict[str, Callable[['PowerUp', int], str]]:
    #     return {
    #         "get_hints": self.get_hints,
    #         "get_percentages",
    #         "skip_question",
    #         "eliminate_half",
    #     }

    @staticmethod
    def sample(
        quiz_assignment: List[QuizAssignment] = -1, name: str = -1, used: bool = -1
    ):
        def if_else(if_val, else_val):
            return if_val if if_val != -1 else else_val

        return PowerUp(
            quiz_assignment=if_else(quiz_assignment, QuizAssignment.sample()),
            name=if_else(name, "PowerUp"),
            used=if_else(used, False),
        )
