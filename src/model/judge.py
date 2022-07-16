from . import db

from model.judge_project_association import association_table

from sqlalchemy.orm import relationship
from sqlalchemy import func


class Judge(db.Model):
    __tablename__ = "judge"

    id = db.Column(db.Integer, primary_key=True)
    judge_address = db.Column(db.String(), nullable=False)
    projects = relationship(
        "Project", secondary=association_table, back_populates="judges")

    creation_date = db.Column(db.DateTime(
        timezone=False), server_default=func.now(), nullable=False)
