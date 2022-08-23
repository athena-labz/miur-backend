import os
import datetime

from dataclasses import dataclass
from pycardano import *
from retry import retry
from typing import Union
from dotenv import load_dotenv

from integration.helpers import ScriptTester


alice_address = Address.from_primitive(
    "addr_test1qzht33q5d3kwf040n0da76pxxkp8wfvjkz88tmf26250pt3mfhguut5gxeuksmf4t8fzjuaevv9xp8485vlusmjndp0qlvplmj")
alice_skey = PaymentSigningKey.from_cbor(
    "58209871491fb8f0aab5de3bcec39643280e7c4360454b8a617270846ea7d83daf59")

bob_address = Address.from_primitive(
    "addr_test1qrjqwhlhl9p8em4axfnmxpwlv4tdegjw5frfl4u8ndwkyy2fvevclv869cf7maj0d8yct07ke2qpns0s7fgpkuyfuahsk3m5ra")
bob_skey = PaymentSigningKey.from_cbor(
    "58209144210de6e95e819c84951fcb810f1dd444164fce1b4bdcfaa8329222b45aa3")

charlie_address = Address.from_primitive(
    "addr_test1qzaj2caww5n3jhmz9gf7fxs4lgnacelt9vtuj0urgl4asdwp0l9pnsm087npfekmnyejqdsjdklcptumurclutxwv7jql9t2nu")
charlie_skey = PaymentSigningKey.from_cbor(
    "5820fbd1a67fb3765fe13321a4b5a3a5f3582dc345cc6f162eb1c296627141f34186")

random_address = Address.from_primitive(
    "addr_test1vq6ugyhv0lwenm0crs4emfq85q9mcltwtawnkgerm6w72tcmpn79y")


mediators_policy = bytes.fromhex(
    "d311d3488cc4fef19d05634adce8534977a3bc6fc18136ad65df1d4f")  # Charlie

target_policy = bytes.fromhex(
    "066a386267eeb9b3b5127a394f1dab770003008fc62719d917947822")  # Alice

fallback_policy = bytes.fromhex(
    "3e3dba78ad40cff962a8d7ee7c6b44f3204abac82a4e408ce639c1b8")  # Bob - REDS


@dataclass
class ContractDatum(PlutusData):
    CONSTR_ID = 0
    mediators: bytes
    target: bytes
    fallback: bytes
    deadline: int


class ScriptTesterEscrowWithTargetToken(ScriptTester):

    def transaction_builder(self, utxo: UTxO, datum: Datum) -> Transaction:
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

        utxos = self._chain_context.utxos(str(alice_address))

        utxo = None
        for utxo_ in utxos:
            if utxo_.output.amount.multi_asset:
                if ScriptHash.from_primitive(target_policy) in utxo_.output.amount.multi_asset:
                    utxo = utxo_

        if utxo is None:
            raise Exception(
                f"Could not find UTxO with token in address {str(alice_address)}")

        builder.add_input(utxo)

        take_output = TransactionOutput(alice_address,
                                        Value.from_primitive(
                                            [
                                                3_000_000,
                                                {
                                                    target_policy: {
                                                        b"GREENS": 1
                                                    }
                                                },
                                            ]
                                        )
                                        )

        builder.add_output(take_output)

        non_nft_utxo = self._find_collateral(alice_address)

        if non_nft_utxo is None:
            self._create_collateral(alice_address, alice_skey)
            non_nft_utxo = self._find_collateral(alice_address)

        builder.collaterals.append(non_nft_utxo)

        signed_tx = builder.build_and_sign([alice_skey], alice_address)

        return signed_tx


class ScriptTesterEscrowWithoutTargetToken(ScriptTester):

    def transaction_builder(self, utxo: UTxO, datum: Datum) -> Transaction:
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

        non_nft_utxo = self._find_collateral(bob_address)

        if non_nft_utxo is None:
            self._create_collateral(bob_address, bob_skey)
            non_nft_utxo = self._find_collateral(bob_address)

        builder.collaterals.append(non_nft_utxo)

        signed_tx = builder.build_and_sign([bob_skey], bob_address)

        return signed_tx


class ScriptTesterFallbackUser(ScriptTester):
    # Medaitor token must be in input and fallback user token must be in output
    # fallback user must receive the full amount inside the script

    # Should test without full amount and then with full amount

    def transaction_builder(self, utxo: UTxO, datum: Datum) -> Transaction:
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

        # charlie utxos
        charlie_utxos = self._chain_context.utxos(str(charlie_address))

        charlie_utxo = None
        for utxo in charlie_utxos:
            if utxo.output.amount.multi_asset:
                if ScriptHash.from_primitive(mediators_policy) in utxo.output.amount.multi_asset:
                    charlie_utxo = utxo.input

        # bob utxos
        bob_utxos = self._chain_context.utxos(str(bob_address))

        bob_utxo = None
        for utxo in bob_utxos:
            if utxo.output.amount.multi_asset:
                if ScriptHash.from_primitive(fallback_policy) in utxo.output.amount.multi_asset:
                    bob_utxo = utxo.input

        builder.add_input_address(charlie_address)

        builder.reference_inputs = [bob_utxo, charlie_utxo]

        charlie_payment_key_hash = PaymentVerificationKey.from_signing_key(charlie_skey).hash()
        builder.required_signers = [charlie_payment_key_hash]

        take_output = TransactionOutput(bob_address, 5_149_265)
        builder.add_output(take_output)

        non_nft_utxo = self._find_collateral(charlie_address)

        if non_nft_utxo is None:
            self._create_collateral(charlie_address, charlie_skey)
            non_nft_utxo = self._find_collateral(charlie_address)

        builder.collaterals.append(non_nft_utxo)

        signed_tx = builder.build_and_sign([charlie_skey], charlie_address)

        return signed_tx


def get_env_val(key):
    load_dotenv()
    val = os.environ.get(key)

    if not val:
        raise Exception(f"Environment variable {key} is not set!")
    return val


script_tester_target_user = ScriptTesterEscrowWithTargetToken(
    get_env_val("BLOCKFROST_ID"),
    Network.TESTNET,
    "deadline2.plutus",
    "keys/alice/payment.skey",
    str(alice_address),
)

script_tester_random_user = ScriptTesterEscrowWithoutTargetToken(
    get_env_val("BLOCKFROST_ID"),
    Network.TESTNET,
    "deadline2.plutus",
    "keys/alice/payment.skey",
    str(alice_address),
)

script_tester_fallback_user_no_mediator = ScriptTesterFallbackUser(
    get_env_val("BLOCKFROST_ID"),
    Network.TESTNET,
    "deadline2.plutus",
    "keys/alice/payment.skey",
    str(alice_address),
)

script_tester_fallback_user_with_mediator = ScriptTesterFallbackUser(
    get_env_val("BLOCKFROST_ID"),
    Network.TESTNET,
    "deadline2.plutus",
    "keys/charlie/payment.skey",
    str(alice_address),
)


def test_contract():
    # Test deadlines
    future = 1691711382000
    past = 1628639382000

    datum = ContractDatum(mediators_policy, target_policy,
                          fallback_policy, past)

    utxo = script_tester_target_user.submit_script(5_149_265, datum)
    assert script_tester_target_user.validate_transaction(utxo, datum) is True

    datum = ContractDatum(mediators_policy, target_policy,
                          fallback_policy, future)
    utxo = script_tester_target_user.submit_script(5_149_265, datum)

    assert script_tester_target_user.validate_transaction(utxo, datum) is False

    # Test receivers
    datum = ContractDatum(mediators_policy, target_policy,
                          fallback_policy, past)

    utxo = script_tester_random_user.submit_script(5_149_265, datum)
    assert script_tester_random_user.validate_transaction(utxo, datum) is False

    # ==================
    datum = ContractDatum(mediators_policy, target_policy,
                          fallback_policy, past)

    script_tester = ScriptTesterFallbackUser(
        get_env_val("BLOCKFROST_ID"),
        Network.TESTNET,
        "deadline2.plutus",
        "keys/alice/payment.skey",
        str(alice_address),
    )

    utxo = script_tester.submit_script(5_149_265, datum)
    assert script_tester.validate_transaction(utxo, datum) is True

    # # Test before deadline with medaitor send to fallback - SUCCED
    # datum = ContractDatum(mediators, target, fallback, past)

    # utxo = script_tester_fallback_user_with_mediator.submit_script(5_149_265, datum)
    # assert script_tester_fallback_user_with_mediator.validate_transaction(utxo, datum) is True

    # # Test after deadline with mediator send to fallback - FAIL
