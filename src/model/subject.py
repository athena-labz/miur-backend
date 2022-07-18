from . import db

from sqlalchemy.orm import relationship

from model.project_subject_association import association_table


class Subject(db.Model):
    __tablename__ = "subject"

    id = db.Column(db.Integer, primary_key=True)

    subject_name = db.Column(db.String(), nullable=False)
    projects = relationship(
        "Project", secondary=association_table, back_populates="subjects")
