from . import db

from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, func
from typing import List, Dict

from .quiz import Quiz
from .user import User


class AttemptAnswer(db.Model):
    __tablename__ = "attempt_answer"

    id = db.Column(db.Integer, primary_key=True)

    attempter_id = db.Column(db.Integer, ForeignKey("user.id"), nullable=False)
    attempter = relationship("User", back_populates="answer_attempts")

    quiz_id = db.Column(db.Integer, ForeignKey("quiz.id"), nullable=False)
    quiz = relationship("Quiz", back_populates="answer_attempts")

    question_index = db.Column(db.Integer, nullable=False)
    answer = db.Column(db.Integer, nullable=False)
    right_answer = db.Column(db.Boolean, nullable=False)

    creation_date = db.Column(
        db.DateTime(timezone=False), server_default=func.now(), nullable=False
    )

    @staticmethod
    def attempt(quiz: Quiz, attempter: User, question_index: int, answer: int):
        attempt_answer = AttemptAnswer(
            attempter_id=attempter.id,
            quiz_id=quiz.id,
            answer=answer,
            question_index=question_index,
            right_answer=quiz.questions[question_index]["right_answer"]
            == answer,
        )

        db.session.add(attempt_answer)
        db.session.commit()

        return attempt_answer

    
    @staticmethod
    def quiz_stats(quiz: Quiz, question_index: int) -> Dict[int, int]:
        query = AttemptAnswer.query.filter(
            AttemptAnswer.quiz_id == quiz.id,
            AttemptAnswer.question_index == question_index,
        )

        stats = query.with_entities(
            AttemptAnswer.answer, func.count(AttemptAnswer.answer)
        ).group_by(AttemptAnswer.answer).all()
        
        print({stat[0]: stat[1] for stat in stats})

        return {stat[0]: stat[1] for stat in stats}
