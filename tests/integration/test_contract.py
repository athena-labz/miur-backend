import os
import datetime

from dataclasses import dataclass
from pycardano import *
from retry import retry
from typing import Union
from dotenv import load_dotenv

from integration.helpers import ScriptTester


@dataclass
class ContractDatum(PlutusData):
    CONSTR_ID = 0
    mediators: bytes
    target: bytes
    fallback: bytes
    deadline: int


class ScriptTesterEscrow(ScriptTester):

    def transaction_builder(self, utxo: UTxO, datum: Datum) -> Transaction:
        # taker_address could be any address. In this example, we will use the same address as giver.
        taker_address = self._sender_address

        # Notice that transaction builder will automatically estimate execution units (num steps & memory) for a redeemer if
        # no execution units are provided in the constructor of Redeemer.
        # Put integer 42 (the secret that unlocks the fund) in the redeemer.
        redeemer = Redeemer(RedeemerTag.SPEND, PlutusData())

        # Current slot - Don't know how to calculate the actual current slot
        # Maybe get the posix time of the last block and use that difference
        current_slot = self._chain_context.last_block_slot

        print("Current slot", current_slot)

        # Our valid range will be of two hours
        hour = 60 * 60

        builder = TransactionBuilder(
            self._chain_context, validity_start=current_slot, ttl=2 * hour)

        builder.add_script_input(
            utxo, PlutusV2Script(self._script), datum, redeemer)

        # Send 5 ADA to taker address. The remaining ADA (~4.7) will be sent as change.
        take_output = TransactionOutput(taker_address, 3_000_000)
        builder.add_output(take_output)

        non_nft_utxo = self._find_collateral(taker_address)

        if non_nft_utxo is None:
            self._create_collateral(taker_address, self._skey)
            non_nft_utxo = self._find_collateral(taker_address)

        builder.collaterals.append(non_nft_utxo)

        signed_tx = builder.build_and_sign([self._skey], taker_address)

        return signed_tx


def get_env_val(key):
    load_dotenv()
    val = os.environ.get(key)

    if not val:
        raise Exception(f"Environment variable {key} is not set!")
    return val


script_tester = ScriptTesterEscrow(
    get_env_val("BLOCKFROST_ID"),
    Network.TESTNET,
    "keys/alice/payment.skey",
    "deadline.plutus",
    "addr_test1qzht33q5d3kwf040n0da76pxxkp8wfvjkz88tmf26250pt3mfhguut5gxeuksmf4t8fzjuaevv9xp8485vlusmjndp0qlvplmj"
)


def test_contract():
    # Fiured out my mistake was that the interval was in posix time ms
    # Now I need to understand why past transaction is failing
    # (maybe compare size > of valid range inside script, like start_range > 1628639382000)
    future = 1691711382000
    past = 1628639382000

    datum = ContractDatum(
        bytes.fromhex(
            "74ad2d482cbf798570abdaf4c22204b2d5ab183e97b2282322427e9f"),
        bytes.fromhex(
            "74ad2d482cbf798570abdaf4c22204b2d5ab183e97b2282322427e9f"),
        bytes.fromhex(
            "74ad2d482cbf798570abdaf4c22204b2d5ab183e97b2282322427e9f"),
        past
    )

    # print(script_tester.transaction_builder())

    utxo = script_tester.submit_script(5_149_265, datum)
    assert script_tester.validate_transaction(utxo, datum) is True

    datum = ContractDatum(
        bytes.fromhex(
            "74ad2d482cbf798570abdaf4c22204b2d5ab183e97b2282322427e9f"),
        bytes.fromhex(
            "74ad2d482cbf798570abdaf4c22204b2d5ab183e97b2282322427e9f"),
        bytes.fromhex(
            "74ad2d482cbf798570abdaf4c22204b2d5ab183e97b2282322427e9f"),
        future
    )
    utxo = script_tester.submit_script(5_149_265, datum)

    assert script_tester.validate_transaction(utxo, datum) is False
