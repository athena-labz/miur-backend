from model import db, ProdUser

from flask import request

import re

def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_regex, email))


def register(email: str):
    data = request.json

    existing_user: ProdUser | None = ProdUser.query.filter(
        ProdUser.email == email
    ).first()

    if existing_user is not None:
        return {
            "message": f"User with email {email} already exists",
            "code": "email-exists",
        }, 400
    
    if len(data["password"]) < 8:
        return {
            "message": "Password must be at least 8 characters long",
            "code": "password-too-short",
        }, 400
    
    if not is_valid_email(email):
        return {
            "message": "Email is not valid",
            "code": "email-not-valid",
        }, 400
    
    user = ProdUser.register(email, data["password"])

    return {}, 200
