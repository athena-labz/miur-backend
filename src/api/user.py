from __future__ import annotations

from flask import request
from sqlalchemy import and_, func

from lib import cardano_tools, auth_tools
from model import User, Quiz, QuizAssignment, db

import datetime
import logging


def register(stake_address: str):
    data = request.json

    existing_user: User | None = User.query.filter(
        User.stake_address == stake_address
    ).first()

    if existing_user is not None:
        return {
            "success": False,
            "message": f"User with stake address {stake_address} already exists",
            "code": "address-exists",
        }, 400

    if not auth_tools.validate_signature(data["signature"], stake_address):
        return {
            "success": False,
            "message": "Invalid signature",
            "code": "invalid-signature",
        }, 400

    user = User(
        stake_address=stake_address,
        payment_address=data["payment_address"],
        email=data["email"],
    )

    db.session.add(user)
    db.session.commit()
    db.session.refresh(user)

    return {"success": True}, 200


def get_info(stake_address: str):
    user: User | None = User.query.filter(User.stake_address == stake_address).first()

    if user is None:
        return {
            "success": False,
            "message": f"Could not find stake address {stake_address}",
            "code": "address-not-found",
        }, 404

    return {
        "stake_address": user.stake_address,
        "payment_address": user.payment_address,
        "email": user.email,
        **(
            {"nft_identifier_policy": user.nft_identifier_policy}
            if user.nft_identifier_policy is not None
            else {}
        ),
    }


def get_quiz_info(stake_address: str):
    user: User | None = User.find(stake_address)
    if user is None:
        return {
            "message": f"Could not find stake address {stake_address}",
            "code": "address-not-found",
        }, 404

    return {
        "created_quizes": [quiz.info() for quiz in Quiz.created_by_user(user)],
        "ongoing_quiz_assignments": [
            assignment.info()
            for assignment in QuizAssignment.query.filter(
                and_(
                    QuizAssignment.assignee == user,
                    QuizAssignment.completed_success == None,
                )
            )
        ],
        "completed_quiz_assignments": [
            assignment.info()
            for assignment in QuizAssignment.query.filter(
                and_(
                    QuizAssignment.assignee == user,
                    QuizAssignment.completed_success != None,
                )
            )
        ],
    }, 200


def get_users():
    data = request.args

    users = (
        User.query.add_columns(
            User.email,
            User.payment_address,
            User.stake_address,
            func.count(User.created_projects).label("project_count"),
        )
        .outerjoin(User.created_projects, isouter=True)
        .group_by(User.id)
        .paginate(
            data["page"] if "page" in data else 0,
            data["count"] if "count" in data else 20,
            False,
        )
    )

    return {
        "users": [
            {
                "email": user.email,
                "stake_address": user.stake_address,
                "payment_address": user.payment_address,
                "project_count": user.project_count,
            }
            for user in users.items
        ],
        "total": users.total,
        "pages": users.pages,
    }
