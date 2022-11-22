from __future__ import annotations
from typing import Dict, Tuple

import pycardano as pyc
import logging


class SignatureMode:
    PaymentMode = 0
    StakeMode = 1


def address_to_pubkeyhash(bech32_addr: str) -> str:
    return pyc.Address.from_primitive(bech32_addr).payment_part.to_primitive().hex()


def signature_message(
    signature: str | dict,
    address: pyc.Address,
    sig_mode: SignatureMode = SignatureMode.StakeMode,
):
    # Returns None if the signature is invalid and the message otherwise

    validation = pyc.verify(signature)

    if validation["verified"] is False:
        logging.warning(f"Validation failed for address {address}")
        logging.warning(validation)
        return None

    if sig_mode == SignatureMode.PaymentMode:
        if (
            validation["signing_address"].payment_part
            != pyc.Address.from_primitive(address).payment_part
        ):
            logging.warning("Signing address different from signature address")
            return None
    else:
        if not pyc.Address.from_primitive(address).staking_part in (
            validation["signing_address"].payment_part,
            validation["signing_address"].staking_part,
        ):
            logging.warning("Signing address different from signature address")
            return None

    return validation["message"]


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
