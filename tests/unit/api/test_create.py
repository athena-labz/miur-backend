from __future__ import annotations

import sys
import helper

from fixtures import api
from model.deliverable import Deliverable
from model.judge import Judge


def test_create(api):
    client, app = api

    sys.path.append("src")

    from model import db, Project

    response = client.post("/projects/create", json=helper.samples.create_project_body)

    assert response.status_code == 200
    assert response.json == {
        "success": True,
        "transaction_cbor": "<cbor>"
    }

    projects = Project.query.all()
    assert len(projects) == 1

    # Make sure project created is equal to the sample provided
    project: Project = projects[0]
    assert project.name == "Project Name"
    assert project.short_description == "Vry sht dscpt"
    assert project.long_description == "Veeeery loooooong descriiiiiiiiptioon"
    assert project.funding_currency == "ADA"
    assert project.funding_achieved == 0
    assert project.funding_expected == 100_000_000_000
    
    assert project.proposer.user_address == "addr_test1qr70n9s9zhfw6p4valvvzc69e0eu7efxtjs6hu786f34rj0lawt235dpfa6sm7hfxevh22p5we3fthwjv5az4pcxr0kqhcndp6"
    assert project.proposer.user_public_key_hash == "fcf9960515d2ed06acefd8c16345cbf3cf65265ca1abf3c7d26351c9"

    deliverable: Deliverable = project.deliverables[0]
    assert deliverable.declaration == "I will do a very good project"
    assert deliverable.duration == 5
    assert deliverable.percentage_requested == 100

    judge: Judge = project.judges[0]
    assert judge.judge_address == "addr_test456"