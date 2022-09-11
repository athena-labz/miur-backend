from flask import request
from dotenv import load_dotenv
from dataclasses import dataclass

from model import Project, User, Subject, Deliverable, db
from lib import auth_tools, cardano_tools

import pycardano as pyc
import datetime
import os


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

    if not "signature" in data:
        return {
            "success": False,
            "message": f"Request body missing signature"
        }, 400

    if auth_tools.user_can_signin(data["signature"], data["creator_address"]) is False:
        return {
            "success": False,
            "message": f"Invalid signature"
        }, 400

    project = Project()

    project.name = data["name"]

    creator = User.query.filter(
        User.address == data["creator_address"]).first()

    if creator is None:
        return {
            "success": False,
            "message": f"User {data['creator_address']} is not registered"
        }, 400

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

    project.start_date = datetime.datetime.utcfromtimestamp(data["start_date"])

    # TODO: Add mediators

    db.session.add(project)
    db.session.commit()

    return {"success": True}, 200


def get_project(project_id):
    project: Project = Project.query.filter(
        Project.project_identifier == project_id).first()

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


def fund_project(project_id: str):
    pass


# def fund_project(project_id: str):
#     data = request.json

#     load_dotenv()

#     BLOCKFROST_PROJECT_ID = os.environ.get("BLOCKFROST_PROJECT_ID")
#     NETWORK_MODE = os.environ.get("NETWORK_MODE")
#     MEDIATOR_POLICY = os.environ.get("MEDIATOR_POLICY")

#     if BLOCKFROST_PROJECT_ID is None:
#         raise ValueError("BLOCKFROST_PROJECT_ID env variable not found")

#     if NETWORK_MODE is None:
#         raise ValueError("NETWORK_MODE env variable not found")

#     if MEDIATOR_POLICY is None:
#         raise ValueError("MEDIATOR_POLICY env variable not found")

#     project: Project = Project.query.filter(
#         Project.project_identifier == project_id).first()

#     if project is None:
#         return {"success": False}, 404

#     chain_context = pyc.BlockFrostChainContext(
#         base_url="https://cardano-mainnet.blockfrost.io/api" if NETWORK_MODE.lower(
#         ) == "mainnet" else "https://cardano-preview.blockfrost.io/api",
#         network=pyc.Network.MAINNET if NETWORK_MODE.lower(
#         ) == "mainnet" else pyc.Network.TESTNET,
#         project_id=BLOCKFROST_PROJECT_ID
#     )

#     with open("script/script.plutus", "r") as f:
#         script_cbor = f.read()

#     # Find target NFT
#     target_policy = project.creator.user_nft_policy

#     mediator_policy = MEDIATOR_POLICY

#     fallback_policy = data["fallback_policy"]

#     # Calculate deadline timestamp

#     # Convert this to UTC
#     project.start_date

#     deadline = undefined

#     @dataclass
#     class ContractDatum(pyc.PlutusData):
#         CONSTR_ID = 0
#         mediators: bytes
#         target: bytes
#         fallback: bytes
#         deadline: int

#     datum = ContractDatum(mediator_policy, target_policy,
#                           fallback_policy, deadline)

#     transaction_cbor = cardano_tools.create_fund_project_transaction(
#         chain_context, script_cbor, data["change_address"], data["utxos"], project.reward_requested, )
