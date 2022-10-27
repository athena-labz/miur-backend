from __future__ import annotations
from lib import cardano_types
from typing import Dict

import pycardano as pyc
import logging
import cbor2


def mint_nfts(
    chain_context: pyc.ChainContext,
    payment_signing_key: pyc.PaymentSigningKey,
    policy_signing_key: pyc.PaymentSigningKey,
    receiver_address: pyc.Address,
    assets: Dict[bytes, int],
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

    policy_verification_key = pyc.PaymentVerificationKey.from_signing_key(
        policy_signing_key
    )

    # A policy that requires a signature from the policy key we generated above
    pub_key_policy = pyc.ScriptPubkey(policy_verification_key.hash())

    policy_id = pub_key_policy.hash()

    # Create a transaction builder
    builder = pyc.TransactionBuilder(chain_context)

    # Add UTxO as input
    builder.add_input_address(payment_address)

    my_assets = pyc.MultiAsset.from_primitive({policy_id.payload: assets})

    # Set nft we want to mint
    builder.mint = my_assets

    # Set native script
    builder.native_scripts = [pub_key_policy]

    attempt_output_value = pyc.Value(2_000_000, my_assets)
    attempt_output = pyc.TransactionOutput(receiver_address, attempt_output_value)

    # min_ada = pyc.min_lovelace_post_alonzo(attempt_output, chain_context)
    min_ada = pyc.min_lovelace(
        chain_context, attempt_output, amount=attempt_output.amount
    )

    if min_ada == 0:
        min_ada = 5_000_000

    output_value = pyc.Value(min_ada, my_assets)
    output = pyc.TransactionOutput(receiver_address, output_value)

    builder.add_output(output)

    if metadata is not None:
        builder.auxiliary_data = pyc.AuxiliaryData(
            pyc.AlonzoMetadata(metadata=pyc.Metadata(metadata))
        )

    if payment_signing_key == policy_signing_key:
        signing_keys = [payment_signing_key]
    else:
        signing_keys = [payment_signing_key, policy_signing_key]

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
    sender_address: pyc.Address,
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
    builder.add_input_address(sender_address)

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

    tx_body = builder.build(change_address=sender_address, merge_change=True)

    return pyc.Transaction(tx_body, pyc.TransactionWitnessSet())


def create_transaction_mediate_project(
    chain_context: pyc.ChainContext,
    mediator_address: pyc.Address,
    mediator_policy: bytes,
    fallback_address: pyc.Address,
    fallback_policy: bytes,
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
        cardano_types.ExecuteFallback(),
    )
    builder.add_input_address(mediator_address)

    sender_utxos = chain_context.utxos(str(mediator_address))

    mediator_utxo = None
    for utxo in sender_utxos:
        if utxo.output.amount.multi_asset:
            if (
                pyc.ScriptHash.from_primitive(mediator_policy)
                in utxo.output.amount.multi_asset
            ):
                mediator_utxo = utxo

    if mediator_utxo is None:
        raise Exception(
            f"Could not find UTxO with mediator token in address {str(mediator_address)}"
        )

    fallback_utxos = chain_context.utxos(str(fallback_address))

    fallback_utxo = None
    for utxo in fallback_utxos:
        if utxo.output.amount.multi_asset:
            if (
                pyc.ScriptHash.from_primitive(fallback_policy)
                in utxo.output.amount.multi_asset
            ):
                fallback_utxo = utxo

    if fallback_utxo is None:
        raise Exception(
            f"Could not find UTxO with token in address {str(fallback_address)}"
        )

    builder.reference_inputs.add(fallback_utxo.input)

    dummy_key: pyc.PaymentSigningKey = pyc.PaymentSigningKey.from_cbor(
        "5820ac29084c8ceca56b02c4118e76c1845c40b5eb810444a069e8edf2f5280ee875"
    )

    transaction = builder.build_and_sign(
        signing_keys=[dummy_key], change_address=fallback_address, merge_change=True
    )
