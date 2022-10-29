import time
import sys
import cbor2
import pytest
from retry import retry

from pycardano import *

import logging

from .base import TEST_RETRIES, TestBase


class TestPlutus(TestBase):

    @retry(tries=TEST_RETRIES, backoff=1.5, delay=3, jitter=(0, 4))
    def test_create_transaction_fallback_project(self):
        sys.path.append("../src")

        from lib import script_tools, cardano_types

        sender_address = Address(self.payment_vkey.hash(), network=self.NETWORK)

        # ----------- Keys -----------
        mediator_skey = SigningKey.from_cbor(
            "58208e1bbd872b4558f7d614e8c5c4593b9ff7a2257b80802e0b50bee71154c6af3f"
        )
        mediator_vkey = VerificationKey.from_signing_key(mediator_skey)
        mediator_address = Address(
            payment_part=mediator_vkey.hash(), network=Network.TESTNET
        )
        mediator_policy = ScriptPubkey(mediator_vkey.hash()).hash().payload

        target_skey = SigningKey.from_cbor(
            "5820b8fbcfca464ddf6865cf28c7c2894902668b0f0a4c0d19da2b7c9bf7649a90b5"
        )
        target_vkey = VerificationKey.from_signing_key(target_skey)
        target_address = Address(
            payment_part=target_vkey.hash(), network=Network.TESTNET
        )
        target_policy = ScriptPubkey(target_vkey.hash()).hash().payload

        fallback_skey = SigningKey.from_cbor(
            "582037021be8046145f1d5b42d50ade182215d59b71d56d4619567424789a877d6f4"
        )
        fallback_vkey = VerificationKey.from_signing_key(fallback_skey)
        fallback_address = Address(
            payment_part=fallback_vkey.hash(), network=Network.TESTNET
        )
        fallback_policy = ScriptPubkey(fallback_vkey.hash()).hash().payload

        # ----------- Mint Script NFT -----------

        script_tools.mint_nfts(
            self.chain_context,
            self.payment_skey,
            [
                (mediator_skey, {b"mediator": (mediator_address, 1)}),
                (target_skey, {b"target": (target_address, 1)}),
                (fallback_skey, {b"fallback": (fallback_address, 1)}),
            ],
        )

        time.sleep(5)

        self.assert_output(
            target_address,
            TransactionOutput(
                address=target_address,
                amount=Value.from_primitive(
                    [
                        5_000_000,
                        {target_policy: {b"target": 1}},
                    ]
                ),
            ),
        )

        self.assert_output(
            fallback_address,
            TransactionOutput(
                address=fallback_address,
                amount=Value.from_primitive(
                    [
                        5_000_000,
                        {fallback_policy: {b"fallback": 1}},
                    ]
                ),
            ),
        )

        self.assert_output(
            mediator_address,
            TransactionOutput(
                address=mediator_address,
                amount=Value.from_primitive(
                    [
                        5_000_000,
                        {mediator_policy: {b"mediator": 1}},
                    ]
                ),
            ),
        )

        # ----------- Giver give ---------------

        with open("../script/script.plutus", "r") as f:
            script_hex = f.read()

            transaction = script_tools.create_transaction_fund_project(
                self.chain_context,
                sender_address,
                10_000_000,
                script_hex,
                mediator_policy,
                target_policy,
                fallback_policy,
                1691711382000,
            )

            escrow_script = cbor2.loads(bytes.fromhex(script_hex))
            script_hash = plutus_script_hash(PlutusV2Script(escrow_script))
            script_address = Address(script_hash, network=self.NETWORK)

        # ----------- Submit Transaction --------------

        # Sign the transaction body hash
        signature = self.payment_skey.sign(transaction.transaction_body.hash())

        # Add verification key and the signature to the witness set
        vk_witnesses = [VerificationKeyWitness(self.payment_vkey, signature)]

        transaction.transaction_witness_set = TransactionWitnessSet(
            vkey_witnesses=vk_witnesses
        )

        signed_tx = Transaction(
            transaction.transaction_body,
            TransactionWitnessSet(vkey_witnesses=vk_witnesses),
        )

        self.chain_context.submit_tx(signed_tx.to_cbor())

        time.sleep(5)

        self.assert_output(
            script_address,
            TransactionOutput(
                address=script_address,
                amount=10_000_000,
                datum_hash=cardano_types.ContractDatum(
                    mediators=mediator_policy,
                    target=target_policy,
                    fallback=fallback_policy,
                    deadline=1691711382000,
                ).hash(),
            ),
        )

        mediator_input = self.chain_context.utxos(str(mediator_address))[0].input
        fallback_input = self.chain_context.utxos(str(fallback_address))[0].input

        script_utxo = self.chain_context.utxos(str(script_address))[0]

        transaction = script_tools.create_transaction_fallback_project(
            self.chain_context,
            mediator_address,
            mediator_input,
            fallback_address,
            fallback_input,
            script_hex,
            script_utxo,
            cardano_types.ContractDatum(
                mediators=mediator_policy,
                target=target_policy,
                fallback=fallback_policy,
                deadline=1691711382000,
            )
        )

        # ----------- Submit Transaction --------------

        # Sign the transaction body hash
        signature = mediator_skey.sign(transaction.transaction_body.hash())

        # Add verification key and the signature to the witness set
        vk_witnesses = [VerificationKeyWitness(mediator_vkey, signature)]

        transaction.transaction_witness_set.vkey_witnesses = vk_witnesses

        self.chain_context.submit_tx(transaction.to_cbor())

        time.sleep(5)

        assert len(self.chain_context.utxos(str(script_address))) == 0

        self.assert_output(
            fallback_address,
            TransactionOutput(fallback_address, 10_000_000),
        )


    # @retry(tries=TEST_RETRIES, backoff=1.5, delay=3, jitter=(0, 4))
    # def test_create_transaction_target_project(self):
    #     sys.path.append("../src")

    #     from lib import script_tools, cardano_types

    #     sender_address = Address(self.payment_vkey.hash(), network=self.NETWORK)

    #     # ----------- Keys -----------
    #     mediator_skey = SigningKey.from_cbor(
    #         "58208e1bbd872b4558f7d614e8c5c4593b9ff7a2257b80802e0b50bee71154c6af3f"
    #     )
    #     mediator_vkey = VerificationKey.from_signing_key(mediator_skey)
    #     mediator_address = Address(
    #         payment_part=mediator_vkey.hash(), network=Network.TESTNET
    #     )
    #     mediator_policy = ScriptPubkey(mediator_vkey.hash()).hash().payload

    #     target_skey = SigningKey.from_cbor(
    #         "5820b8fbcfca464ddf6865cf28c7c2894902668b0f0a4c0d19da2b7c9bf7649a90b5"
    #     )
    #     target_vkey = VerificationKey.from_signing_key(target_skey)
    #     target_address = Address(
    #         payment_part=target_vkey.hash(), network=Network.TESTNET
    #     )
    #     target_policy = ScriptPubkey(target_vkey.hash()).hash().payload

    #     fallback_skey = SigningKey.from_cbor(
    #         "582037021be8046145f1d5b42d50ade182215d59b71d56d4619567424789a877d6f4"
    #     )
    #     fallback_vkey = VerificationKey.from_signing_key(fallback_skey)
    #     fallback_address = Address(
    #         payment_part=fallback_vkey.hash(), network=Network.TESTNET
    #     )
    #     fallback_policy = ScriptPubkey(fallback_vkey.hash()).hash().payload

    #     # ----------- Mint Script NFT -----------

    #     script_tools.mint_nfts(
    #         self.chain_context,
    #         self.payment_skey,
    #         [
    #             (mediator_skey, {b"mediator": (mediator_address, 1)}),
    #             (target_skey, {b"target": (target_address, 1)}),
    #             (fallback_skey, {b"fallback": (fallback_address, 1)}),
    #         ],
    #     )

    #     time.sleep(5)

    #     self.assert_output(
    #         target_address,
    #         TransactionOutput(
    #             address=target_address,
    #             amount=Value.from_primitive(
    #                 [
    #                     5_000_000,
    #                     {target_policy: {b"target": 1}},
    #                 ]
    #             ),
    #         ),
    #     )

    #     self.assert_output(
    #         fallback_address,
    #         TransactionOutput(
    #             address=fallback_address,
    #             amount=Value.from_primitive(
    #                 [
    #                     5_000_000,
    #                     {fallback_policy: {b"fallback": 1}},
    #                 ]
    #             ),
    #         ),
    #     )

    #     self.assert_output(
    #         mediator_address,
    #         TransactionOutput(
    #             address=mediator_address,
    #             amount=Value.from_primitive(
    #                 [
    #                     5_000_000,
    #                     {mediator_policy: {b"mediator": 1}},
    #                 ]
    #             ),
    #         ),
    #     )

    #     # ----------- Giver give ---------------

    #     with open("../script/script.plutus", "r") as f:
    #         script_hex = f.read()

    #         transaction = script_tools.create_transaction_fund_project(
    #             self.chain_context,
    #             sender_address,
    #             10_000_000,
    #             script_hex,
    #             mediator_policy,
    #             target_policy,
    #             fallback_policy,
    #             1628639382000,
    #         )

    #         escrow_script = cbor2.loads(bytes.fromhex(script_hex))
    #         script_hash = plutus_script_hash(PlutusV2Script(escrow_script))
    #         script_address = Address(script_hash, network=self.NETWORK)

    #     # ----------- Submit Transaction --------------

    #     # Sign the transaction body hash
    #     signature = self.payment_skey.sign(transaction.transaction_body.hash())

    #     # Add verification key and the signature to the witness set
    #     vk_witnesses = [VerificationKeyWitness(self.payment_vkey, signature)]

    #     transaction.transaction_witness_set = TransactionWitnessSet(
    #         vkey_witnesses=vk_witnesses
    #     )

    #     signed_tx = Transaction(
    #         transaction.transaction_body,
    #         TransactionWitnessSet(vkey_witnesses=vk_witnesses),
    #     )

    #     self.chain_context.submit_tx(signed_tx.to_cbor())

    #     time.sleep(5)

    #     self.assert_output(
    #         script_address,
    #         TransactionOutput(
    #             address=script_address,
    #             amount=10_000_000,
    #             datum_hash=cardano_types.ContractDatum(
    #                 mediators=mediator_policy,
    #                 target=target_policy,
    #                 fallback=fallback_policy,
    #                 deadline=1628639382000,
    #             ).hash(),
    #         ),
    #     )

    #     target_input = self.chain_context.utxos(str(target_address))[0].input

    #     script_utxo = self.chain_context.utxos(str(script_address))[0]

    #     transaction = script_tools.create_transaction_target_project(
    #         self.chain_context,
    #         target_address,
    #         target_input,
    #         script_hex,
    #         script_utxo,
    #         cardano_types.ContractDatum(
    #             mediators=mediator_policy,
    #             target=target_policy,
    #             fallback=fallback_policy,
    #             deadline=1628639382000,
    #         )
    #     )

    #     # ----------- Submit Transaction --------------

    #     # Sign the transaction body hash
    #     signature = mediator_skey.sign(transaction.transaction_body.hash())

    #     # Add verification key and the signature to the witness set
    #     vk_witnesses = [VerificationKeyWitness(mediator_vkey, signature)]

    #     transaction.transaction_witness_set.vkey_witnesses = vk_witnesses

    #     self.chain_context.submit_tx(transaction.to_cbor())

    #     time.sleep(5)

    #     assert len(self.chain_context.utxos(str(script_address))) == 0

    #     self.assert_output(
    #         target_address,
    #         TransactionOutput(target_address, 10_000_000),
    #     )
