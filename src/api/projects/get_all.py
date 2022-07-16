from flask import request
from lib import api_tools
from model import Project, ProjectState


def get_all():
    data = request.args

    # Defaults
    count = 100 if not "count" in data else data["count"]
    page = 1 if not "page" in data else data["page"]
    order = "desc" if not "order" in data else data["order"]

    if order == "asc":
        query = Project.query.join(ProjectState).order_by(
            ProjectState.creation_date.asc())
    else:
        query = Project.query.join(ProjectState).order_by(
            ProjectState.creation_date.desc())

    projects = query.paginate(
        page=int(page),
        per_page=int(count),
        max_per_page=int(count),
    )

    return {
        "count": projects.query.count(),
        "projects": [api_tools.parse_project_short(project) for project in projects.items]
    }, 200
