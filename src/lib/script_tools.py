from __future__ import annotations
from lib import cardano_types
from typing import Dict, Tuple, List
from dotenv import load_dotenv

import pycardano as pyc
import logging
import cbor2
import sys
import os


def mint_nfts(
    chain_context: pyc.ChainContext,
    payment_signing_key: pyc.PaymentSigningKey,
    assets: Dict[pyc.PaymentSigningKey, Dict[bytes, Tuple[pyc.Address, int]]],
    metadata: dict = None,
):
    logging.info("*** Minting NFT!")

    payment_verification_key = pyc.PaymentVerificationKey.from_signing_key(
        payment_signing_key
    )
    payment_address = pyc.Address(
        payment_part=payment_verification_key.hash(), network=pyc.Network.TESTNET
    )

    logging.info(f"Using payment address {payment_address}")

    # Create a transaction builder
    builder = pyc.TransactionBuilder(chain_context)

    # Add UTxO as input
    builder.add_input_address(payment_address)

    signing_keys = [payment_signing_key]

    builder.native_scripts = []

    multi_asset_dict = {}
    for skey, tokens in assets:
        multi_asset_tokens = {}
        for asset_name, addr_amount in tokens.items():
            multi_asset_tokens[asset_name] = addr_amount[1]

        policy_verification_key = pyc.PaymentVerificationKey.from_signing_key(skey)

        # A policy that requires a signature from the policy key we generated above
        pub_key_policy = pyc.ScriptPubkey(policy_verification_key.hash())

        policy_id = pub_key_policy.hash()

        multi_asset_dict[policy_id.payload] = multi_asset_tokens
        builder.native_scripts.append(pub_key_policy)

        if not skey in signing_keys:
            signing_keys.append(skey)

        output_value = pyc.Value(
            5_000_000,
            pyc.MultiAsset.from_primitive({policy_id.payload: multi_asset_tokens}),
        )
        output = pyc.TransactionOutput(
            pyc.Address(
                payment_part=policy_verification_key.hash(), network=pyc.Network.TESTNET
            ),
            output_value,
        )

        builder.add_output(output)

    my_assets = pyc.MultiAsset.from_primitive(multi_asset_dict)

    # Set nft we want to mint
    builder.mint = my_assets

    if metadata is not None:
        builder.auxiliary_data = pyc.AuxiliaryData(
            pyc.AlonzoMetadata(metadata=pyc.Metadata(metadata))
        )

    signed_tx = builder.build_and_sign(
        signing_keys=signing_keys,
        change_address=payment_address,
        merge_change=False,
    )

    logging.info(f"submitting signed transaction to chain - TxID: {signed_tx.id}")
    logging.debug("############### Transaction created ###############")
    logging.debug(signed_tx)
    logging.debug(signed_tx.to_cbor())

    # Submit signed transaction to the network
    logging.debug("############### Submitting transaction ###############")

    chain_context.submit_tx(signed_tx.to_cbor())

    return signed_tx


def create_transaction_fund_project(
    chain_context: pyc.ChainContext,
    registered_address: pyc.Address,
    funding_utxos: List[pyc.UTxO],
    funding_amount: pyc.Value,
    script_hex: str,
    mediator_policy: bytes,
    target_policy: bytes,
    fallback_policy: bytes,
    deadline: int,
):
    escrow_script = cbor2.loads(bytes.fromhex(script_hex))
    script_hash = pyc.plutus_script_hash(pyc.PlutusV2Script(escrow_script))
    script_address = pyc.Address(script_hash, network=pyc.Network.TESTNET)

    builder = pyc.TransactionBuilder(chain_context)

    for utxo in funding_utxos:
        builder.add_input(utxo)

    datum = cardano_types.ContractDatum(
        mediators=mediator_policy,
        target=target_policy,
        fallback=fallback_policy,
        deadline=deadline,
    )

    builder.add_output(
        pyc.TransactionOutput(
            address=script_address,
            amount=funding_amount,
            datum_hash=pyc.datum_hash(datum),
        )
    )

    builder.required_signers = [registered_address.payment_part]

    tx_body = builder.build(change_address=registered_address, merge_change=True)

    return pyc.Transaction(tx_body, pyc.TransactionWitnessSet())


def create_transaction_fallback_project(
    chain_context: pyc.ChainContext,
    mediator_address: pyc.Address,
    mediator_input: pyc.TransactionInput,
    fallback_address: pyc.Address,
    fallback_input: pyc.TransactionInput,
    script_hex: str,
    script_utxo: pyc.UTxO,
    script_datum: pyc.Datum,
):
    escrow_script = cbor2.loads(bytes.fromhex(script_hex))
    script_hash = pyc.plutus_script_hash(pyc.PlutusV1Script(escrow_script))
    script_address = pyc.Address(script_hash, network=pyc.Network.TESTNET)

    # Current slot - Don't know how to calculate the actual current slot
    # Maybe get the posix time of the last block and use that difference
    current_slot = chain_context.last_block_slot

    print("Current slot", current_slot)

    # Our valid range will be of two hours
    hour = 60 * 60

    builder = pyc.TransactionBuilder(
        chain_context, validity_start=current_slot, ttl=2 * hour
    )

    builder.required_signers = [mediator_address.payment_part]

    builder.add_script_input(
        script_utxo,
        pyc.PlutusV2Script(escrow_script),
        script_datum,
        pyc.Redeemer(
            pyc.RedeemerTag.SPEND,
            cardano_types.ExecuteFallback(),
            ex_units=pyc.ExecutionUnits(1549238, 442841802),
        ),
    )
    builder.add_input_address(mediator_address)

    builder.reference_inputs.add(mediator_input)
    builder.reference_inputs.add(fallback_input)

    builder.add_output(
        pyc.TransactionOutput(fallback_address, script_utxo.output.amount)
    )

    dummy_key: pyc.PaymentSigningKey = pyc.PaymentSigningKey.from_cbor(
        "5820ac29084c8ceca56b02c4118e76c1845c40b5eb810444a069e8edf2f5280ee875"
    )

    transaction = builder.build_and_sign(
        signing_keys=[dummy_key], change_address=mediator_address, merge_change=True
    )

    return transaction


def create_transaction_target_project(
    chain_context: pyc.ChainContext,
    target_address: pyc.Address,
    target_input: pyc.TransactionInput,
    script_hex: str,
    script_utxo: pyc.UTxO,
    script_datum: pyc.Datum,
):
    escrow_script = cbor2.loads(bytes.fromhex(script_hex))
    script_hash = pyc.plutus_script_hash(pyc.PlutusV1Script(escrow_script))
    script_address = pyc.Address(script_hash, network=pyc.Network.TESTNET)

    # Current slot - Don't know how to calculate the actual current slot
    # Maybe get the posix time of the last block and use that difference
    current_slot = chain_context.last_block_slot

    print("Current slot", current_slot)

    # Our valid range will be of two hours
    hour = 60 * 60

    builder = pyc.TransactionBuilder(
        chain_context, validity_start=current_slot, ttl=2 * hour
    )

    builder.add_script_input(
        script_utxo,
        pyc.PlutusV2Script(escrow_script),
        script_datum,
        pyc.Redeemer(
            pyc.RedeemerTag.SPEND,
            cardano_types.ExecuteTarget(),
        ),
    )
    builder.add_input_address(target_address)

    builder.reference_inputs.add(target_input)

    builder.add_output(pyc.TransactionOutput(target_address, script_utxo.output.amount))

    dummy_key: pyc.PaymentSigningKey = pyc.PaymentSigningKey.from_cbor(
        "5820ac29084c8ceca56b02c4118e76c1845c40b5eb810444a069e8edf2f5280ee875"
    )

    transaction = builder.build_and_sign(
        signing_keys=[dummy_key], change_address=target_address, merge_change=False
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