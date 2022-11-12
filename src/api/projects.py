from flask import request
from sqlalchemy import and_, or_

from model import Project, User, Subject, Deliverable, Funding, db
from lib import auth_tools


def get_projects():
    data = request.args

    # Defaults
    count = 100 if not "count" in data else data["count"]
    page = 1 if not "page" in data else data["page"]
    order = "desc" if not "order" in data else data["order"]

    creator = data["creator"] if "creator" in data else None
    funder = data["funder"] if "funder" in data else None

    if creator is not None and funder is not None:
        query = Project.query.filter(
            or_(
                Project.creator.has(User.address == creator),
                Project.funding.any(Funding.funder.has(User.address == funder)),
            )
        )
    elif creator is not None:
        query = Project.query.filter(Project.creator.has(User.address == creator))
    elif funder is not None:
        query = Project.query.filter(
            Project.funding.any(Funding.funder.has(User.address == funder))
        )
    else:
        query = Project.query

    if order == "asc":
        query = query.order_by(Project.creation_date.asc())
    else:
        query = query.order_by(Project.creation_date.desc())

    projects = query.paginate(
        page=int(page),
        per_page=int(count),
        max_per_page=int(count),
    )

    return {
        "count": projects.query.count(),
        "projects": [
            {
                "project_id": project.project_identifier,
                "name": project.name,
                "creator": {
                    "id": project.creator.user_identifier,
                    "email": project.creator.email,
                    "address": project.creator.address,
                },
                "mediators": [
                    {
                        "id": mediator.user_identifier,
                        "email": mediator.email,
                        "address": mediator.address,
                    }
                    for mediator in project.mediators
                ],
                "short_description": project.short_description,
                "long_description": project.long_description,
                "subjects": [subject.subject_name for subject in project.subjects],
                "deliverables": [
                    deliverable.deliverable for deliverable in project.deliverables
                ],
                "days_to_complete": project.days_to_complete,
            }
            for project in projects.items
        ],
    }, 200


def create_project():
    data = request.json

    if not "signature" in data:
        return {"success": False, "message": f"Request body missing signature"}, 400

    if auth_tools.user_can_signin(data["signature"], data["creator"]) is False:
        return {"success": False, "message": f"Invalid signature"}, 400

    project = Project()

    project.name = data["name"]

    creator = User.query.filter(User.address == data["creator"]).first()

    if creator is None:
        return {
            "success": False,
            "message": f"User {data['creator']} is not registered",
        }, 400

    # TODO: Enforce that creator has identity NFT

    project.creator = creator

    project.short_description = data["short_description"]
    project.long_description = data["long_description"]

    project.days_to_complete = data["days_to_complete"]

    mediators = []
    for mediator_email in data["mediators"]:
        user = User.query.filter(User.email == mediator_email).first()
        if user is None:
            return {
                "success": False,
                "message": f"Mediator {mediator_email} is not registered",
            }, 404

        mediators.append(user)

    project.mediators = mediators

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
            "project_id": project.project_identifier,
            "name": project.name,
            "creator": {
                "id": project.creator.user_identifier,
                "email": project.creator.email,
                "address": project.creator.address,
            },
            "short_description": project.short_description,
            "long_description": project.long_description,
            "subjects": [subject.subject_name for subject in project.subjects],
            "days_to_complete": project.days_to_complete,
            "deliverables": [
                deliverable.deliverable for deliverable in project.deliverables
            ],
            "mediators": [
                {
                    "id": mediator.user_identifier,
                    "email": mediator.email,
                    "address": mediator.address,
                }
                for mediator in project.mediators
            ],
        },
    }, 200


def get_project_user(project_id, address):
    project: Project = Project.query.filter(
        Project.project_identifier == project_id
    ).first()

    if project is None:
        return {"message": f"Project with project id {project_id} not found!"}, 404

    user: User = User.query.filter(User.address == address).first()

    if user is None:
        return {"message": f"User with address {address} not found!"}, 404

    funding: Funding = Funding.query.filter(
        and_(
            Funding.funder_id == user.id,
            Funding.project_id == project.id,
            or_(Funding.status == "submitted", Funding.status == "onchain"),
        )
    ).first()

    return {
        "funder": funding is not None,
        "creator": project.creator_id == user.id,
        "mediator": user in project.mediators,
    }, 200
