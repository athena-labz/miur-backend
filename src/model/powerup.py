from . import db

from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, func
from typing import List, Callable, Dict, Any

from .quiz_assignment import QuizAssignment
from .attempt_answer import AttemptAnswer

import random
import copy


class PowerUp(db.Model):
    __tablename__ = "powerup"

    id = db.Column(db.Integer, primary_key=True)

    quiz_assignment_id = db.Column(
        db.Integer, ForeignKey("quiz_assignment.id"), nullable=False
    )
    quiz_assignment = relationship("QuizAssignment", back_populates="powerups")

    name = db.Column(db.String, nullable=False)

    # If a powerup was used, we should save a payload
    used = db.Column(db.Boolean, default=False, nullable=False)
    payload = db.Column(db.JSON, nullable=True)

    question_index_used = db.Column(db.Integer, nullable=True)

    def info(self):
        return {
            "name": self.name,
            "used": self.used,
            "payload": self.payload,
            "question_index_used": self.question_index_used,
        }

    def get_hints(self, question_index: int) -> str:
        random.seed(self.id)

        return {
            "hint": random.choice(
                self.quiz_assignment.quiz.questions[question_index]["hints"]
            )
        }

    def get_percentages(self, question_index: int) -> Dict[int, float]:
        random.seed(self.id)

        stats = AttemptAnswer.quiz_stats(self.quiz_assignment.quiz, question_index)

        total = sum(stats.values())

        # Avoid division by zero
        if total == 0:
            result = [
                0
                for _ in range(
                    len(self.quiz_assignment.quiz.questions[question_index]["answers"])
                )
            ]
        else:
            # Result should include very possible choice (0% if no one has chosen it)
            result = [
                stats.get(i, 0) / total
                for i, _ in enumerate(
                    self.quiz_assignment.quiz.questions[question_index]["answers"]
                )
            ]

        return {"percentages": result}

    def skip_question(self, question_index: int = None):
        # Returns the right answer for this question index

        return {
            "answer": self.quiz_assignment.quiz.questions[question_index][
                "right_answer"
            ],
        }

    def eliminate_half(self, question_index: int) -> Dict[str, List[str]]:
        random.seed(self.id)

        questions_copy = copy.deepcopy(self.quiz_assignment.quiz.questions)

        # Make sure we don't eliminate the right answer
        choices = questions_copy[question_index]["answers"]
        right_answer = questions_copy[question_index]["right_answer"]

        answer_content = choices[right_answer]

        # Remove right answer by index
        del choices[right_answer]

        # Eliminate half of the choices
        remainder = random.sample(choices, len(choices) // 2)

        remainder.append(answer_content)
        # remainder = sorted(remainder)

        result = []
        for choice in self.quiz_assignment.quiz.questions[question_index]["answers"]:
            if choice in remainder:
                result.append(choice)
            else:
                result.append(None)

        return {"remaining_choices": result}

    def powerups_map(self) -> Dict[str, Callable[["PowerUp", int], dict]]:
        return {
            "get_hints": self.get_hints,
            "get_percentages": self.get_percentages,
            "skip_question": self.skip_question,
            "eliminate_half": self.eliminate_half,
        }

    def use_powerup(self) -> Dict[str, Any]:
        if self.used is False:
            self.question_index_used = self.quiz_assignment.current_question

        powerup = self.powerups_map()[self.name](self.question_index_used)

        if self.used is False:
            self.used = True
            self.payload = powerup

            db.session.add(self)
            db.session.commit()

        return powerup

    @staticmethod
    def create(quiz_assignment: QuizAssignment, name: str):
        powerup = PowerUp(
            quiz_assignment=quiz_assignment,
            name=name,
        )

        db.session.add(powerup)
        db.session.commit()

        return powerup

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
