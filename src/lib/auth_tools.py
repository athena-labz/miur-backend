import datetime
import logging

from lib import cardano_tools
from model import User


EXPIRE_SECONDS = 24 * 60 * 60


def validate_signature(signature, address):
    validation = cardano_tools.signature_message(signature, address)
    logging.warning("BLOPOS")
    if validation is None:
        logging.warning(
            "Validation failed - Either address is incorrect or signature is invalid")
        return False

    if not validation.startswith("Athena MIUR | ") and len(validation) < 14:
        logging.warning(
            "Signature is formatted incorrectly - does not start with \"Athena MIUR | \" or does not have a continuation")
        return False

    try:
        timestamp = int(validation[14:])
    except ValueError:
        logging.warning("Invalid timestamp given - cannot convert to integer")
        return False

    current_date_unix = int(
        (datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

    logging.warning(abs(current_date_unix - timestamp))
    if abs(current_date_unix - timestamp) > EXPIRE_SECONDS:
        logging.warning(f"Invalid timestamp given - timestamp outside of the {EXPIRE_SECONDS} seconds range")
        return False

    logging.warning("WTH? How is this possible?")

    return True


def user_can_signin(signature, address):
    if validate_signature(signature, address) is False:
        return False

    logging.warning(address)
    logging.warning([user.address for user in User.query.all()])

    user = User.query.filter(User.address == address).first()
    if user is None:
        logging.warning("User not found!")
        return False

    return True
