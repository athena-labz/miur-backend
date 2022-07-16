from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .project import Project
from .judge import Judge
from .user import User
from .fund import Fund
from .deliverable import Deliverable
from .project_state import ProjectState