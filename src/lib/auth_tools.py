import datetime

from lib import cardano_tools
from model import User


def validate_signature(signature, address):
    validation = cardano_tools.signature_message(signature, address)

    if validation is None:
        print(
            "Validation failed - Either address is incorrect or signature is invalid")
        return False

    if not validation.startswith("Athena MIUR | ") and len(validation) < 14:
        print(
            "Signature is formatted incorrectly - does not start with \"Athena MIUR | \" or does not have a continuation")
        return False

    try:
        timestamp = int(validation[14:])
    except ValueError:
        print("Invalid timestamp given - cannot convert to integer")
        return False

    current_date_unix = int(
        (datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

    print(abs(current_date_unix - timestamp))
    if abs(current_date_unix - timestamp) > 60:
        print("Invalid timestamp given - timestamp outside of the 60 seconds range")
        return False

    return True


def user_can_signin(signature, address):
    if validate_signature(signature, address) is False:
        return False

    user = User.query.filter(User.address == address).first()
    if user is None:
        return False

    return True
