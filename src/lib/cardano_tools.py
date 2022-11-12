from pycardano import Address
from pycardano.cip.cip8 import verify

import logging


def address_to_pubkeyhash(bech32_addr: str) -> str:
    return Address.from_primitive(bech32_addr).payment_part.to_primitive().hex()


def signature_message(signature, address):
    # Returns None if the signature is invalid and the message otherwise

    validation = verify(signature)

    if validation["verified"] is False:
        logging.warning(f"Validation failed for address {address}")
        logging.warning(validation)
        return None

    if (
        validation["signing_address"].payment_part
        != Address.from_primitive(address).staking_part
    ):
        return None

    return validation["message"]
