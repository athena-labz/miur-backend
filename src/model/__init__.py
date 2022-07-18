from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .project import Project
from .user import User