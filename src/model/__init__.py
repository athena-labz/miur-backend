from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .project import Project
from .subject import Subject
from .deliverable import Deliverable
from .user import User