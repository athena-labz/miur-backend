import importlib

from flask import request
from lib import config, api_tools
from model import db, Fund, Project, User


config = config.load_config()

provider = config["athena_provider"]
athena_provider = importlib.import_module(f"athena_providers.{provider}")


def fund(project_id):
    # Find project w/ project id
    project = Project.query.filter(
        Project.project_identifier == project_id).first()

    if project is None:
        return {
            "message": f"Project ID {project_id} not found!"
        }, 404

    # Getting query params
    data = request.args

    if not "user" in data:
        return {
            "message": "User not provided as query parameter!"
        }, 404

    
    if not "amount" in data:
        return {
            "message": "Amount not provided as query parameter!"
        }, 404

    # Find user w/ user addr
    user = User.query.filter(User.user_address == data["user"]).first()

    if user is None:
        user = api_tools.create_user(data["user"])

        if user is None:
            return {
                "success": False,
                "message": f"Invalid bech32 address {data['user']}!"
            }
        
        db.session.add(user)
        db.session.commit()

    # Create fund
    fund = Fund()

    fund.funder = user
    fund.project = project

    fund.funding_amount = data["amount"]
    fund.status = "draft"

    db.session.add(fund)
    db.session.commit()

    project_result = athena_provider.create_project(None)

    tx_hash = project_result["tx_hash"]
    tx_cbor = project_result["tx_cbor"]

    return {
        "success": True,
        "transaction_cbor": tx_cbor
    }, 200
