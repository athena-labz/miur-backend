from __future__ import annotations
from lib import cardano_types
from typing import Dict, Tuple, List
from dotenv import load_dotenv

import pycardano as pyc
import logging
import cbor2
import sys
import os


def create_transaction_fund_project(
    chain_context: pyc.ChainContext,
    registered_address: pyc.Address,
    funding_utxos: List[pyc.UTxO],
    funding_amount: pyc.Value,
    script_hex: str,
    mediator_policy: bytes,
    target_address: pyc.Address,
    deadline: int,
):
    escrow_script = cbor2.loads(bytes.fromhex(script_hex))
    script_hash = pyc.plutus_script_hash(pyc.PlutusV2Script(escrow_script))
    script_address = pyc.Address(script_hash, network=pyc.Network.TESTNET)

    print("Address", script_address)

    builder = pyc.TransactionBuilder(chain_context)

    total_value = pyc.Value(0)

    target_value = funding_amount
    if isinstance(target_value, int):
        target_value = pyc.Value(target_value)

    for utxo in funding_utxos:
        builder.add_input(utxo)

    datum = pyc.IndefiniteList(
        [target_address.payment_part.to_primitive(), mediator_policy, deadline]
    )

    builder.add_output(
        pyc.TransactionOutput(
            address=script_address,
            amount=funding_amount,
            datum_hash=pyc.datum_hash(datum),
        )
    )

    tx_body = builder.build(change_address=registered_address, merge_change=True)

    return pyc.Transaction(tx_body, pyc.TransactionWitnessSet())


def create_transaction_fallback_project(
    chain_context: pyc.ChainContext,
    collateral_input: pyc.UTxO,
    mediator_address: pyc.Address,
    mediator_input: pyc.TransactionInput,
    fallback_address: pyc.Address,
    script_hex: str,
    script_utxo: pyc.UTxO,
    script_datum: pyc.Datum,
):
    escrow_script = cbor2.loads(bytes.fromhex(script_hex))

    # Current slot - Don't know how to calculate the actual current slot
    # Maybe get the posix time of the last block and use that difference
    current_slot = chain_context.last_block_slot

    print("Current slot", current_slot)

    builder = pyc.TransactionBuilder(chain_context)

    builder.collaterals = [collateral_input]

    # Range [current_slot, current_slot+1]
    builder.validity_start = current_slot
    builder.ttl = current_slot + 2 * 60

    builder.required_signers = [mediator_address.payment_part]

    builder.add_script_input(
        script_utxo,
        pyc.PlutusV2Script(escrow_script),
        script_datum,
        pyc.Redeemer(
            pyc.RedeemerTag.SPEND,
            cardano_types.SendToFallback(reference_input_index=0),
        ),
    )
    builder.reference_inputs.add(mediator_input)

    dummy_key: pyc.PaymentSigningKey = pyc.PaymentSigningKey.from_cbor(
        "5820ac29084c8ceca56b02c4118e76c1845c40b5eb810444a069e8edf2f5280ee875"
    )

    transaction = builder.build_and_sign(
        signing_keys=[dummy_key], change_address=fallback_address
    )

    return transaction


def create_transaction_target_project(
    chain_context: pyc.ChainContext,
    target_address: pyc.Address,
    collateral_input: pyc.UTxO,
    script_hex: str,
    script_utxo: pyc.UTxO,
    script_datum: pyc.Datum,
):
    escrow_script = cbor2.loads(bytes.fromhex(script_hex))

    # Current slot - Don't know how to calculate the actual current slot
    # Maybe get the posix time of the last block and use that difference
    current_slot = chain_context.last_block_slot

    print("Current slot", current_slot)

    builder = pyc.TransactionBuilder(chain_context)

    builder.collaterals = [collateral_input]

    # Range [current_slot, current_slot+1]
    builder.validity_start = current_slot
    builder.ttl = current_slot + 2 * 60

    builder.add_script_input(
        script_utxo,
        pyc.PlutusV2Script(escrow_script),
        script_datum,
        pyc.Redeemer(
            pyc.RedeemerTag.SPEND,
            cardano_types.SendToTarget(),
        ),
    )

    builder.required_signers = [target_address.payment_part]

    dummy_key: pyc.PaymentSigningKey = pyc.PaymentSigningKey.from_cbor(
        "5820ac29084c8ceca56b02c4118e76c1845c40b5eb810444a069e8edf2f5280ee875"
    )

    transaction = builder.build_and_sign(
        signing_keys=[dummy_key], change_address=target_address, merge_change=True
    )

    return transaction


def initialise_cardano():
    # Initialise env variables, if any of them are not
    # here, raise exception
    sys.path.append("src")
    load_dotenv()

    envs = {}
    for env in [
        "BLOCKFROST_PROJECT_ID",
        "BLOCKFROST_BASE_URL",
        "NETWORK_MODE",
        "SCRIPT_PATH",
        "MEDIATOR_POLICY",
    ]:
        val = os.environ.get(env)
        if val is None:
            raise ValueError(f"Env variable {env} not found!")

        envs[env] = val

    # ChainContext will depend on the environment variables
    chain_context = pyc.BlockFrostChainContext(
        project_id=envs["BLOCKFROST_PROJECT_ID"],
        base_url=envs["BLOCKFROST_BASE_URL"],
        network=pyc.Network.MAINNET
        if envs["NETWORK_MODE"].lower() == "mainnet"
        else pyc.Network.TESTNET,
    )

    with open(envs["SCRIPT_PATH"], "r") as f:
        script = f.read()

    return {
        "chain_context": chain_context,
        "script": script,
        "mediator_policy": envs["MEDIATOR_POLICY"],
    }


def cbor_to_utxo(utxo_cbor: str) -> pyc.UTxO:
    cbor_lst = cbor2.loads(bytes.fromhex(utxo_cbor))
    transaction_input_cbor_bytes = cbor2.dumps(cbor_lst[0])
    transaction_output_cbor_bytes = cbor2.dumps(cbor_lst[1])

    utxo = pyc.UTxO(
        pyc.TransactionInput.from_cbor(transaction_input_cbor_bytes),
        pyc.TransactionOutput.from_cbor(transaction_output_cbor_bytes),
    )

    return utxo
