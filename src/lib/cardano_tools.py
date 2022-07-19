from pycardano import Address
from pycardano.cip.cip8 import verify


def address_to_pubkeyhash(bech32_addr: str) -> str:
    return Address.from_primitive(bech32_addr).payment_part.to_primitive().hex()


def signature_message(signature, address):
    # Returns None if the signature is invalid and the message otherwise

    validation = verify(signature)

    if validation["verified"] is False:
        return None

    if str(validation["signing_address"]) != address:
        return None

    return validation["message"]