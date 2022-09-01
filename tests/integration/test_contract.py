import os
import datetime

from dataclasses import dataclass
from pycardano import *
from retry import retry
from typing import Union
from dotenv import load_dotenv

import integration.helpers as helpers
# from integration.helpers import ScriptTesterTarget, ScriptTesterTargetNoToken


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


mediator_policy = bytes.fromhex(
    "55166d7398d10d879b2b253fbb5b4010e39fec67dc62ca348335e377")  # Charlie

target_policy = bytes.fromhex(
    "06743756d03e59bf245416f7220034f5336aaa33153e5b67b75c402f")  # Alice

fallback_policy = bytes.fromhex(
    "80c73937cf44cb818b932a8073925d711320086eaa5c6ab6dde0e941")  # Bob - REDS


@dataclass
class ContractDatum(PlutusData):
    CONSTR_ID = 0
    mediators: bytes
    target: bytes
    fallback: bytes
    deadline: int


def get_env_val(key):
    load_dotenv()
    val = os.environ.get(key)

    if not val:
        raise Exception(f"Environment variable {key} is not set!")
    return val


def test_contract():
    # Test deadlines
    future = 1691711382000
    past = 1628639382000

    # ATTENTION: We are validating the future datum not the past one
    # TODO: Fix this

    datum = ContractDatum(mediator_policy, target_policy,
                          fallback_policy, past)

    script_tester = helpers.ScriptTesterTarget(
        get_env_val("BLOCKFROST_ID"),
        Network.TESTNET,
        "script/script.plutus",
        "keys/alice/payment.skey",
        str(alice_address),
    )

    utxo = script_tester.submit_script(5_149_265, datum)
    assert script_tester.validate_transaction(utxo, datum) is True

    # Receiver has not token (should have target token)
    script_tester = helpers.ScriptTesterTargetNoToken(
        get_env_val("BLOCKFROST_ID"),
        Network.TESTNET,
        "script/script.plutus",
        "keys/alice/payment.skey",
        str(alice_address),
    )

    utxo = script_tester.submit_script(5_149_265, datum)
    assert script_tester.validate_transaction(utxo, datum) is False

    # Receiver doesn't have right target token (has another one)
    script_tester = helpers.ScriptTesterTargetWrongToken(
        get_env_val("BLOCKFROST_ID"),
        Network.TESTNET,
        "script/script.plutus",
        "keys/alice/payment.skey",
        str(alice_address),
    )

    utxo = script_tester.submit_script(5_149_265, datum)
    assert script_tester.validate_transaction(utxo, datum) is False

    # Wrong output value
    script_tester = helpers.ScriptTesterTargetWrongOutputValue(
        get_env_val("BLOCKFROST_ID"),
        Network.TESTNET,
        "script/script.plutus",
        "keys/alice/payment.skey",
        str(alice_address),
    )

    utxo = script_tester.submit_script(5_149_265, datum)
    assert script_tester.validate_transaction(utxo, datum) is False

    # Wrong output address
    script_tester = helpers.ScriptTesterTargetWrongOutputAddress(
        get_env_val("BLOCKFROST_ID"),
        Network.TESTNET,
        "script/script.plutus",
        "keys/alice/payment.skey",
        str(alice_address),
    )

    utxo = script_tester.submit_script(5_149_265, datum)
    assert script_tester.validate_transaction(utxo, datum) is False

    # Before deadline
    future_datum = ContractDatum(mediator_policy, target_policy,
                          fallback_policy, future)

    script_tester = helpers.ScriptTesterTarget(
        get_env_val("BLOCKFROST_ID"),
        Network.TESTNET,
        "script/script.plutus",
        "keys/alice/payment.skey",
        str(alice_address),
    )

    utxo = script_tester.submit_script(5_149_265, future_datum)
    assert script_tester.validate_transaction(utxo, future_datum) is False