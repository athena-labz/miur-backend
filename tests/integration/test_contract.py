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


class ScriptTesterEscrowWithToken(ScriptTester):

    def transaction_builder(self, utxo: UTxO, datum: Datum) -> Transaction:
        sender_address = self._sender_address
        
        # taker_address could be any address. In this example, we will use the same address as giver.
        taker_address = sender_address

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

        utxos = self._chain_context.utxos(str(sender_address))
        utxo = None
        for utxo_ in utxos:
            if utxo_.output.amount.multi_asset:
                utxo = utxo_

        builder.add_input(utxo)

        take_output = TransactionOutput(taker_address,
            Value.from_primitive(
                [
                    3_000_000,
                    {
                        bytes.fromhex(
                            "066a386267eeb9b3b5127a394f1dab770003008fc62719d917947822"  # Policy ID
                        ): {
                            b"GREENS": 1  # Asset name and amount
                        }
                    },
                ]
            )
        )

        builder.add_output(take_output)

        non_nft_utxo = self._find_collateral(sender_address)

        if non_nft_utxo is None:
            self._create_collateral(sender_address, self._skey)
            non_nft_utxo = self._find_collateral(sender_address)

        builder.collaterals.append(non_nft_utxo)

        signed_tx = builder.build_and_sign([self._skey], taker_address)

        return signed_tx


class ScriptTesterEscrowWithoutToken(ScriptTester):

    def transaction_builder(self, utxo: UTxO, datum: Datum) -> Transaction:
        sender_address = self._sender_address
        
        # taker_address could be any address. In this example, we will use the same address as giver.
        taker_address = sender_address

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

        non_nft_utxo = self._find_collateral(sender_address)

        if non_nft_utxo is None:
            self._create_collateral(sender_address, self._skey)
            non_nft_utxo = self._find_collateral(sender_address)

        builder.collaterals.append(non_nft_utxo)

        signed_tx = builder.build_and_sign([self._skey], taker_address)

        return signed_tx


def get_env_val(key):
    load_dotenv()
    val = os.environ.get(key)

    if not val:
        raise Exception(f"Environment variable {key} is not set!")
    return val

sender_address = "addr_test1qzht33q5d3kwf040n0da76pxxkp8wfvjkz88tmf26250pt3mfhguut5gxeuksmf4t8fzjuaevv9xp8485vlusmjndp0qlvplmj"
receiver_address_validate = sender_address
receiver_address_fail = "addr_test1vq6ugyhv0lwenm0crs4emfq85q9mcltwtawnkgerm6w72tcmpn79y"

script_tester_validate = ScriptTesterEscrowWithToken(
    get_env_val("BLOCKFROST_ID"),
    Network.TESTNET,
    "keys/alice/payment.skey",
    "deadline2.plutus",
    sender_address,
)

script_tester_invalidate = ScriptTesterEscrowWithoutToken(
    get_env_val("BLOCKFROST_ID"),
    Network.TESTNET,
    "keys/alice/payment.skey",
    "deadline2.plutus",
    sender_address,
)


def test_contract():
    # Test deadlines 
    future = 1691711382000
    past = 1628639382000

    datum = ContractDatum(
        bytes.fromhex(
            "066a386267eeb9b3b5127a394f1dab770003008fc62719d917947822"),
        bytes.fromhex(
            "066a386267eeb9b3b5127a394f1dab770003008fc62719d917947822"),
        bytes.fromhex(
            "066a386267eeb9b3b5127a394f1dab770003008fc62719d917947822"),
        past
    )

    utxo = script_tester_validate.submit_script(5_149_265, datum)
    assert script_tester_validate.validate_transaction(utxo, datum) is True

    datum = ContractDatum(
        bytes.fromhex(
            "066a386267eeb9b3b5127a394f1dab770003008fc62719d917947822"),
        bytes.fromhex(
            "066a386267eeb9b3b5127a394f1dab770003008fc62719d917947822"),
        bytes.fromhex(
            "066a386267eeb9b3b5127a394f1dab770003008fc62719d917947822"),
        future
    )
    utxo = script_tester_validate.submit_script(5_149_265, datum)

    assert script_tester_validate.validate_transaction(utxo, datum) is False

    # Test receivers
    datum = ContractDatum(
        bytes.fromhex(
            "066a386267eeb9b3b5127a394f1dab770003008fc62719d917947822"),
        bytes.fromhex(
            "066a386267eeb9b3b5127a394f1dab770003008fc62719d917947822"),
        bytes.fromhex(
            "066a386267eeb9b3b5127a394f1dab770003008fc62719d917947822"),
        past
    )

    utxo = script_tester_invalidate.submit_script(5_149_265, datum)
    assert script_tester_invalidate.validate_transaction(utxo, datum) is False
