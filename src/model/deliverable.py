from . import db


class Deliverable(db.Model):
    __tablename__ = "deliverable"

    id = db.Column(db.Integer, primary_key=True)
    deliverable = db.Column(db.String(), nullable=False)
