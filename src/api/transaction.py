from typing import List
from flask import request
from sqlalchemy import and_

from lib import script_tools, auth_tools
from model import Project, User, Funding, db

import pycardano as pyc


SECONDS_FOR_DAY = 86_400


def fund_project():
    # Initialise Cardano needs to give us
    # * Chain Context
    # * Script Hex
    # * Mediator Policy

    # Parameters we are getting from the user
    # * Address or Email of funder - Some sort of unique user identification
    # * Funding Amount
    # * ID from the project he is funding

    # I'm Alice, I am authenticated with address addr1 and email alice@email.com

    # I have signed the transaction with addr1, but I have another address where
    # my NFT is located - addr2

    # When I sign this transaction should app enforce that NFT is in addr1 or is
    # it okay to be in addr2?

    # Yes, but all transaction should request the signature from the original
    # address

    # * Chain Context we will get based on our environment variables
    # * Sender address we are getting based on the funder identifier
    # * Funding Amount we are getting from the API body
    # * Script Hex getting based on env variables
    # * Mediator Policy getting based on env variables
    # * Target Policy getting based on the user from that created
    # the project with the ID given in the request body params
    # * Falbback getting based on the funder identifier
    # * Deadline getting from the project wsith the given project ID

    data = request.json

    stake_address = data["stake_address"]
    funding_utxos = data["funding_utxos"]
    funding_amount = data["funding_amount"]
    project_id = data["project_id"]
    signature = data["signature"]

    if not auth_tools.validate_signature(signature, stake_address):
        return {
            "success": False,
            "message": "Invalid signature",
            "code": "invalid-signature",
        }, 400

    project: Project = Project.query.filter(
        and_(Project.project_identifier == project_id, Project.status == "open")
    ).first()

    if project is None:
        return {
            "message": f"No open project found with ID {project_id}",
            "code": "project-not-found",
        }, 404

    funder: User = User.query.filter(User.stake_address == stake_address).first()
    if funder is None:
        return {
            "message": f"No registered user found with address {stake_address}",
            "code": "address-not-found",
        }, 404

    cardano_handler = script_tools.initialise_cardano()

    transaction = script_tools.create_transaction_fund_project(
        cardano_handler["chain_context"],
        pyc.Address.from_primitive(funder.payment_address),
        [script_tools.cbor_to_utxo(utxo) for utxo in funding_utxos],
        funding_amount,
        cardano_handler["script"],
        bytes.fromhex(cardano_handler["mediator_policy"]),
        pyc.Address.from_primitive(project.creator.payment_address),
        project.creation_date.timestamp() + project.days_to_complete * SECONDS_FOR_DAY,
    )

    funding = Funding(
        funder=funder,
        project=project,
        transaction_hash=str(transaction.transaction_body.id),
        transaction_index=0,
        amount=funding_amount,
    )

    db.session.add(funding)
    db.session.commit()

    # Sender will need to have the identifier NFT in this case
    return {
        "transaction_cbor": transaction.transaction_body.to_cbor(),
        "witness_cbor": transaction.transaction_witness_set.to_cbor(),
    }, 200


def fund_project_submitted():
    data = request.json

    stake_address = data["stake_address"]
    transaction_hash = data["transaction_hash"]
    signature = data["signature"]

    # Make sure address exists
    funder: User = User.query.filter(User.stake_address == stake_address).first()
    if funder is None:
        return {
            "message": f"No registered user found with address {stake_address}",
            "code": "address-not-found",
        }, 404

    # Make sure funding with transaction hash exists
    funding: Funding = Funding.query.filter(
        Funding.transaction_hash == transaction_hash
    ).first()

    if funding is None:
        return {
            "message": f"No funding transaction found with hash {transaction_hash}",
            "code": "funding-not-found",
        }, 404

    if not auth_tools.validate_signature(signature, stake_address):
        return {
            "message": "Invalid signature",
            "code": "invalid-signature",
        }, 400

    funding.status = "submitted"

    db.session.add(funding)
    db.session.commit()

    return {"message": "Everything went well"}, 200
