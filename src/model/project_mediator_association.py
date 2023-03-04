from . import db


association_table = db.Table(
    "project_mediator_association",
    db.metadata,
    db.Column("project_id", db.ForeignKey("project.id"), primary_key=True),
    db.Column("user_id", db.ForeignKey("user.id"), primary_key=True),
)
