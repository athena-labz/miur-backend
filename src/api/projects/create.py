import importlib
import logging

from lib import config, cardano_tools
from flask import request
from model import db, Project, Deliverable, User
from model.judge import Judge

config = config.load_config()

provider = config["athena_provider"]
athena_provider = importlib.import_module(f"athena_providers.{provider}")


def create():
    data = request.json

    project = Project()
    project.name = data["name"]
    project.short_description = data["short_description"]
    project.long_description = data["long_description"]
    project.funding_currency = data["funding_currency"]
    project.funding_expected = data["funding_expected"]

    proposer = User()
    proposer.user_address = data["project_proposer"]

    try:
        proposer.user_public_key_hash = cardano_tools.address_to_pubkeyhash(
            data["project_proposer"])
    except TypeError as e:
        logging.info(f"Error handled while trying to convert address to public key hash!")
        return {
            "success": False,
            "message": f"Invalid address {data['project_proposer']}!"
        }, 200
    except Exception as e:
        raise e
    
    project.proposer = proposer

    deliverables = []
    for i, data_deliverable in enumerate(data["deliverables"]):
        deliverable = Deliverable()

        deliverable.deliverable_index = i
        deliverable.declaration = data_deliverable["declaration"]
        deliverable.duration = data_deliverable["duration"]
        deliverable.percentage_requested = data_deliverable["percentage_requested"]

        deliverables.append(deliverable)

    project.deliverables = deliverables

    judges = []
    for address in data["judges"]:
        judge = Judge()

        judge.judge_address = address

        judges.append(judge)
    
    project.judges = judges

    db.session.add(project)
    db.session.commit()

    project_result = athena_provider.create_project(None)

    tx_hash = project_result["tx_hash"]
    tx_cbor = project_result["tx_cbor"]

    return {
        "success": True,
        "transaction_cbor": tx_cbor
    }, 200
