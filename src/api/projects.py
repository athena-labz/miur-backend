from flask import request

from model import Project


def get_projects():
    data = request.args

    # Defaults
    count = 100 if not "count" in data else data["count"]
    page = 1 if not "page" in data else data["page"]
    order = "desc" if not "order" in data else data["order"]

    if order == "asc":
        query = Project.query.order_by(Project.creation_date.asc())
    else:
        query = Project.query.order_by(Project.creation_date.desc())

    projects = query.paginate(
        page=int(page),
        per_page=int(count),
        max_per_page=int(count),
    )

    return {
        "count": projects.query.count(),
        "projects": [{
            "name": project.name,
            "creator_address": project.creator.address,
            "short_description": project.short_description,
            "subjects": [subject.subject_name for subject in project.subjects],
            "reward_requested": project.reward_requested,
            "days_to_complete": project.days_to_complete,
            "collateral": project.collateral,
        } for project in projects.items]
    }, 200

def create_project():
    pass