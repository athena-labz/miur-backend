from . import db


association_table = db.Table('project_subject_association', db.metadata,
                             db.Column('project_id', db.ForeignKey(
                                 'project.id'), primary_key=True),
                             db.Column('subject_id', db.ForeignKey(
                                 'subject.id'), primary_key=True)
                             )
