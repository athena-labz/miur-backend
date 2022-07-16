from __future__ import annotations

from model import Project, User
from lib import cardano_tools

import logging


def parse_project_short(project: Project) -> dict:
    return {
        "name": project.name,
        "short_description": project.short_description,
        "funding_currency": project.funding_currency,
        "funding_achieved": project.funding_achieved,
        "funding_expected": project.funding_expected,
        "project_proposer": project.proposer.user_address,
    }

def parse_project_long(project: Project) -> dict:
    return {
        "name": project.name,
        "short_description": project.short_description,
        "long_description": project.long_description,
        "funding_currency": project.funding_currency,
        "funding_achieved": project.funding_achieved,
        "funding_expected": project.funding_expected,
        "project_proposer": project.proposer.user_address,
        "deliverables": [{
            "declaration": deliverable.declaration,
            "duration": deliverable.duration,
            "percentage_requested": deliverable.percentage_requested
        } for deliverable in project.deliverables],
        "judges": [judge.judge_address for judge in project.judges]
    }

def create_user(bech32_addr: str) -> User:
    user = User()

    user.user_address = bech32_addr

    try:
        user.user_public_key_hash = cardano_tools.address_to_pubkeyhash(bech32_addr)
    except TypeError as e:
        logging.info(f"Error handled while trying to convert address {bech32_addr} to public key hash!")
        logging.info(e)

        return None
    except Exception as e:
        raise e

    return user