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

    min_ada = pyc.min_lovelace_post_alonzo(attempt_output, chain_context)

    logging.warning("min ada" + min_ada)

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
    script_hash = pyc.plutus_script_hash(pyc.PlutusV1Script(escrow_script))
    script_address = pyc.Address(script_hash, network=chain_context.network)

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
