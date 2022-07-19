from flask import request

from model import Project, User, Subject, Deliverable, db


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
            "project_id": project.project_identifier,
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
    data = request.json

    project = Project()

    project.name = data["name"]

    creator = User()
    creator.address = data["creator_address"]
    creator.public_key_hash = "blahblahblah"

    project.creator = creator

    project.short_description = data["short_description"]
    project.long_description = data["long_description"]

    project.reward_requested = data["reward_requested"]
    project.days_to_complete = data["days_to_complete"]
    project.collateral = data["collateral"]

    subjects = []
    for data_subject in data["subjects"]:
        subject = Subject()
        subject.subject_name = data_subject

        subjects.append(subject)

    project.subjects = subjects

    deliverables = []
    for data_deliverable in data["deliverables"]:
        deliverable = Deliverable()
        deliverable.deliverable = data_deliverable

        deliverables.append(deliverable)

    project.deliverables = deliverables

    # TODO: Add mediators

    db.session.add(project)
    db.session.commit()

    return {"success": True}, 200


def get_project(project_id):
    project = Project.query.filter(Project.project_identifier == project_id).first()

    if project is None:
        return {"success": False}, 404
    
    return {
        "success": True,
        "project": {
            "name": project.name,
            "creator_address": project.creator.address,
            "short_description": project.short_description,
            "long_description": project.long_description,
            "subjects": [subject.subject_name for subject in project.subjects],
            "reward_requested": project.reward_requested,
            "days_to_complete": project.days_to_complete,
            "collateral": project.collateral,
            "deliverables": [deliverable.deliverable for deliverable in project.deliverables],
            "mediators": [mediator.address for mediator in project.mediators],
        }
    }, 200