from __future__ import annotations

from pycardano import Address
from pycardano.cip.cip8 import verify
from typing import List, Union

import pycardano as pyc
import cbor2


def address_to_pubkeyhash(bech32_addr: str) -> str:
    return Address.from_primitive(bech32_addr).payment_part.to_primitive().hex()


def signature_message(signature, address):
    # Returns None if the signature is invalid and the message otherwise

    validation = verify(signature)

    if validation["verified"] is False:
        return None

    if (
        validation["signing_address"].payment_part
        != Address.from_primitive(address).payment_part
    ):
        return None

    return validation["message"]


def create_fund_project_transaction(
    chain_context: pyc.ChainContext,
    script_cbor: str,
    change_address: pyc.Address,
    sender_utxos: List[pyc.UTxO],
    amount: Union[int, pyc.Value],
    datum: pyc.Datum
):
    builder = pyc.TransactionBuilder(chain_context)

    for sender_utxo in sender_utxos:
        builder.add_input(sender_utxo)

    script = cbor2.loads(bytes.fromhex(script_cbor))
    script_address = Address(
        pyc.plutus_script_hash(pyc.PlutusV2Script(script)),
        network=chain_context.network,
    )

    builder.add_output(
        pyc.TransactionOutput(script_address, amount,
                              datum_hash=pyc.datum_hash(datum)),
        datum=datum,
        add_datum_to_witness=True,
    )

    tx_body = builder.build(change_address=change_address)


    # pyc.Transaction.from_cbor("")

    return pyc.Transaction(tx_body, pyc.TransactionWitnessSet())
