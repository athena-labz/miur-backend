from typing import List
from flask import request
from sqlalchemy import and_

from lib import script_tools
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

    registered_address = data["registered_address"]
    funding_utxos = data["funding_utxos"]
    funding_amount = data["funding_amount"]
    project_id = data["project_id"]

    project: Project = Project.query.filter(
        and_(Project.project_identifier == project_id, Project.status == "open")
    ).first()

    if project is None:
        return {"message": f"No open project found with ID {project_id}"}, 404

    funder: User = User.query.filter(
        User.address == registered_address).first()
    if funder is None:
        return {
            "message": f"No registered user found with address {registered_address}"
        }, 404

    if funder.nft_identifier_policy is None:
        return {"message": f"User {funder.address} has not any identity NFTs yet!"}, 400

    project_creator_nft = project.creator.nft_identifier_policy
    if project_creator_nft is None:
        return {
            "message": f"Cannot fund project whose creator has no identity NFTs!"
        }, 400

    cardano_handler = script_tools.initialise_cardano()

    transaction = script_tools.create_transaction_fund_project(
        cardano_handler["chain_context"],
        pyc.Address.from_primitive(registered_address),
        [script_tools.cbor_to_utxo(utxo) for utxo in funding_utxos],
        funding_amount,
        cardano_handler["script"],
        bytes.fromhex(cardano_handler["mediator_policy"]),
        bytes.fromhex(project_creator_nft),
        bytes.fromhex(funder.nft_identifier_policy),
        project.creation_date.timestamp() + project.days_to_complete * SECONDS_FOR_DAY,
    )

    funding = Funding(
        funder=funder,
        project=project,
        transaction_hash=str(transaction.transaction_body.id)
    )

    db.session.add(funding)
    db.session.commit()

    # Sender will need to have the identifier NFT in this case
    return {
        "transaction_cbor": transaction.transaction_body.to_cbor(),
        "witness_cbor": transaction.transaction_witness_set.to_cbor(),
    }, 200
