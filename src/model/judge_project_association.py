from . import db


association_table = db.Table('association', db.metadata,
    db.Column('project_id', db.ForeignKey('project.id'), primary_key=True),
    db.Column('judge_id', db.ForeignKey('judge.id'), primary_key=True)
)