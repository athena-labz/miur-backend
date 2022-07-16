from pycardano import Address


def address_to_pubkeyhash(bech32_addr: str) -> str:
    return Address.from_primitive(bech32_addr).payment_part.to_primitive().hex()
