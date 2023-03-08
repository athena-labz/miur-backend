from flask import request
from sqlalchemy import and_, or_
from typing import Union

from model import Project, User, Subject, Submission, Deliverable, Funding, Review, db
from lib import auth_tools


import datetime


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
                Project.creator.has(User.stake_address == creator),
                Project.funding.any(Funding.funder.has(User.stake_address == funder)),
            )
        )
    elif creator is not None:
        query = Project.query.filter(Project.creator.has(User.stake_address == creator))
    elif funder is not None:
        query = Project.query.filter(
            Project.funding.any(Funding.funder.has(User.stake_address == funder))
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
        "projects": [project.parse() for project in projects.items],
    }, 200


def create_project():
    data = request.json

    if not "signature" in data:
        return {"success": False, "message": f"Request body missing signature"}, 400

    if auth_tools.user_can_signin(data["signature"], data["creator"]) is False:
        return {"success": False, "message": f"Invalid signature"}, 400

    project = Project()

    project.name = data["name"]

    creator = User.query.filter(User.stake_address == data["creator"]).first()

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
    for mediator_stake_address in data["mediators"]:
        user = User.query.filter(User.stake_address == mediator_stake_address).first()
        if user is None:
            return {
                "success": False,
                "message": f"Mediator {mediator_stake_address} is not registered",
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
        return {"success": False, "code": "address-not-found"}, 404

    return {
        "success": True,
        "project": project.parse(),
    }, 200


def get_project_user(project_id, stake_address):
    project: Project = Project.query.filter(
        Project.project_identifier == project_id
    ).first()

    if project is None:
        return {"message": f"Project with project id {project_id} not found!"}, 404

    user: User = User.query.filter(User.stake_address == stake_address).first()

    if user is None:
        return {
            "message": f"User with address {stake_address} not found!",
            "code": "address-not-found",
        }, 404

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


def submit_project(project_id):
    data = request.json

    project = Project.query.filter(Project.project_identifier == project_id).first()
    if project is None:
        return {
            "success": False,
            "code": "project_not_found",
            "message": f"Project with identifier {project_id} not found",
        }, 404

    if (
        auth_tools.user_can_signin(data["signature"], project.creator.stake_address)
        is False
    ):
        return {
            "success": False,
            "code": "invalid_signature",
            "message": f"Invalid signature",
        }, 400

    submission = Submission(
        project=project,
        title=data["title"],
        content=data["content"],
    )

    project.submissions.append(submission)

    db.session.add(project)
    db.session.commit()

    return {"success": True}, 200


def submit_review(submission_id):
    data = request.json

    reviewer = User.query.filter(User.stake_address == data["reviewer"]).first()
    if reviewer is None:
        return {
            "success": False,
            "code": "user_not_found",
            "message": f"User with stake address {data['reviewer']} not found",
        }, 404

    if auth_tools.user_can_signin(data["signature"], data["reviewer"]) is False:
        return {
            "success": False,
            "code": "invalid_signature",
            "message": f"Invalid signature",
        }, 400

    submission: Union[Submission, None] = Submission.query.filter(
        Submission.submission_identifier == submission_id
    ).first()

    if submission is None:
        return {
            "success": False,
            "code": "submission_not_found",
            "message": f"Submission {submission_id} not found",
        }, 404

    review = Review(
        reviewer=reviewer,
        submission=submission,
        approval=data["approval"],
        review=data["review"],
        deadline=datetime.datetime.utcfromtimestamp(data["deadline"]),
    )

    submission.review = review

    db.session.add(submission)
    db.session.commit()

    return {"success": True}, 200


def get_submissions(project_id):
    project = Project.query.filter(Project.project_identifier == project_id).first()
    if project is None:
        return {
            "success": False,
            "code": "project_not_found",
            "message": f"Project with identifier {project_id} not found",
        }, 404

    return {
        "count": len(project.submissions),
        "submissions": [submission.parse() for submission in project.submissions],
    }, 200
