from __future__ import annotations

import os
import sys
import datetime
import pycardano as pyc

from fixtures import api
from typing import List


def test_fund_project(api, monkeypatch):
    client, app = api

    from model import User, Project, Subject, Deliverable, Funding, db

    monkeypatch.setattr("lib.auth_tools.validate_signature", lambda *_: True)

    os.environ = {
        **os.environ,
        "MEDIATOR_POLICY": "e1b6ffd66d966a4ba1b5de07189f0784cbceda9574c87e62c2382f63",
    }

    alice = User(
        email="alice@email.com",
        payment_address="addr_test1vpacm899akkpck3u0zmjndfsppapqrxstqq38nwvm0xv7wcjxzzqy",
        stake_address="stake_test123",
        nft_identifier_policy="7b8d9ca5edac1c5a3c78b729b530087a100cd0580113cdccdbcccf3b",
    )

    bob = User(
        email="bob@email.com",
        payment_address="addr_test1vrsmdl7kdktx5japkh0qwxylq7zvhnk6j46vslnzcguz7cc7cyz6j",
        stake_address="stake_test456",
    )

    charlie = User(
        email="charlie@email.com",
        payment_address="addr_test1vpfwv0ezc5g8a4mkku8hhy3y3vp92t7s3ul8g778g5yegsgalc6gc",
        stake_address="stake_test789",
        nft_identifier_policy="6c29e3e756a5f7794792340b94b1426bab9ad61d87061a8c369f2009",
    )

    project = Project()
    project.project_identifier = "project_id"
    project.creator = alice
    project.subjects = [Subject(subject_name="Math"), Subject(subject_name="Tourism")]

    project.name = "Project"

    project.short_description = "lorem ipsum..."
    project.long_description = "lorem ipsum dolor sit amet..."

    project.days_to_complete = 15

    project.deliverables = [
        Deliverable(deliverable="I am going to do it"),
        Deliverable(deliverable="I am doint it I swear"),
    ]
    project.mediators = [bob]

    project.creation_date = datetime.datetime(2022, 6, 24, 12, 0, 0)

    with app.app_context():
        db.session.add(project)
        db.session.add(charlie)
        db.session.commit()
        db.session.refresh(project)
        db.session.refresh(charlie)

    class MockWitnessSet:
        def to_cbor(self):
            return "<cbor>"

    class MockTransactionBody:
        id = pyc.TransactionId.from_primitive(
            "c6bb2a88f6f7cc27390788ca80dbd3b851558e004033585df1581f060afafdaf"
        )

        def to_cbor(self):
            return "<cbor>"

    class MockTransaction:
        transaction_body = MockTransactionBody()
        transaction_witness_set = MockWitnessSet()

    class MockChainContext(pyc.ChainContext):
        def __init__(self, *args, **kwargs):
            pass

    mock_chain_context = MockChainContext()

    monkeypatch.setattr("pycardano.BlockFrostChainContext", MockChainContext)

    mock_function_environment = {}

    def update_environment(args):
        mock_function_environment["create_transaction_fund_project"] = args

        return MockTransaction()

    monkeypatch.setattr(
        "api.transaction.script_tools.create_transaction_fund_project",
        lambda *args: update_environment(args),
    )

    monkeypatch.setattr(
        "api.transaction.script_tools.initialise_cardano",
        lambda: {
            "chain_context": mock_chain_context,
            "script": "<script>",
            "mediator_policy": "e1b6ffd66d966a4ba1b5de07189f0784cbceda9574c87e62c2382f63",
        },
    )

    fallback_address = "addr_test1vpfwv0ezc5g8a4mkku8hhy3y3vp92t7s3ul8g778g5yegsgalc6gc"
    fallback_funding_address = (
        "addr_test1vzpwq95z3xyum8vqndgdd9mdnmafh3djcxnc6jemlgdmswcve6tkw"
    )

    utxo = pyc.UTxO(
        pyc.TransactionInput(
            pyc.TransactionId.from_primitive(
                "5e0cba9e817823ce82c32ded0b22f6790f075cd39ae9e0ab9af7ad1cc81edf17"
            ),
            0,
        ),
        pyc.TransactionOutput(
            pyc.Address.from_primitive(fallback_funding_address), 10_000_000
        ),
    )

    res = client.post(
        "/transaction/projects/fund",
        json={
            "stake_address": "stake_test789",
            "funding_utxos": [utxo.to_cbor()],
            "funding_amount": 10_000_000,
            "project_id": "project_id",
            "signature": "sig"
        },
    )

    print(res.json)
    assert res.status_code == 200
    assert res.json == {"transaction_cbor": "<cbor>", "witness_cbor": "<cbor>"}

    assert "create_transaction_fund_project" in mock_function_environment

    assert (
        mock_function_environment["create_transaction_fund_project"][0]
        == mock_chain_context
    )

    assert mock_function_environment["create_transaction_fund_project"][
        1
    ] == pyc.Address.from_primitive(fallback_address)

    assert mock_function_environment["create_transaction_fund_project"][2] == [utxo]

    assert mock_function_environment["create_transaction_fund_project"][3] == 10_000_000

    assert mock_function_environment["create_transaction_fund_project"][4] == "<script>"

    assert mock_function_environment["create_transaction_fund_project"][
        5
    ] == bytes.fromhex("e1b6ffd66d966a4ba1b5de07189f0784cbceda9574c87e62c2382f63")

    assert mock_function_environment["create_transaction_fund_project"][
        6
    ] == bytes.fromhex("7b8d9ca5edac1c5a3c78b729b530087a100cd0580113cdccdbcccf3b")

    assert mock_function_environment["create_transaction_fund_project"][
        7
    ] == bytes.fromhex("6c29e3e756a5f7794792340b94b1426bab9ad61d87061a8c369f2009")

    assert (
        mock_function_environment["create_transaction_fund_project"][8]
        == 1_656_082_800 + 15 * 86_400
    )

    funding: List[Funding] = Funding.query.all()
    assert len(funding) == 1

    fund = funding[0]
    assert fund.funder_id == charlie.id
    assert fund.project_id == project.id
    assert (
        fund.transaction_hash
        == "c6bb2a88f6f7cc27390788ca80dbd3b851558e004033585df1581f060afafdaf"
    )
    assert fund.transaction_index == 0
    assert fund.amount == 10_000_000
    assert fund.status == "requested"


def test_fund_project_submitted(api, monkeypatch):
    client, app = api

    sys.path.append("src")

    class NewDate(datetime.datetime):
        @classmethod
        def utcnow(cls):
            return cls(2022, 1, 1, 0, 0, 0)

    monkeypatch.setattr(
        "api.user.datetime.datetime",
        NewDate,
    )

    monkeypatch.setattr("lib.auth_tools.validate_signature", lambda *_: True)

    from model import db, User, Funding, Project, Subject, Deliverable

    project = Project()
    project.project_identifier = "project_id"
    project.creator = User(
        email="alice@email.com",
        payment_address="addr_test123",
        stake_address="stake_test123",
    )
    project.subjects = [Subject(subject_name="Math"), Subject(subject_name="Tourism")]

    project.name = "Project"

    project.short_description = "lorem ipsum..."
    project.long_description = "lorem ipsum dolor sit amet..."

    project.days_to_complete = 15

    project.deliverables = [
        Deliverable(deliverable="I am going to do it"),
        Deliverable(deliverable="I am doint it I swear"),
    ]
    project.mediators = [
        User(
            email="bob@email.com",
            payment_address="addr_test456",
            stake_address="stake_test456",
        )
    ]

    project.creation_date = datetime.datetime(2022, 6, 24, 12, 0, 0)

    with app.app_context():
        db.session.add(project)
        db.session.commit()
        db.session.refresh(project)

    charlie = User(
        email="charlie@email.com",
        payment_address="addr_test123",
        stake_address="stake_test789",
    )

    funding = Funding(
        funder=charlie,
        project=project,
        transaction_hash="hash",
        transaction_index=0,
        amount=10_000_000,
    )

    with app.app_context():
        db.session.add(funding)
        db.session.commit()
        db.session.refresh(funding)

    response = client.post(
        "/transaction/projects/fund/submitted",
        json={
            "stake_address": "stake_test789",
            "transaction_hash": "hash",
            "signature": "sig",
        },
    )

    assert response.status_code == 200

    fundings = Funding.query.all()

    assert len(fundings) == 1
    assert fundings[0].status == "submitted"
