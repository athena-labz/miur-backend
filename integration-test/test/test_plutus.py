import time
import sys
import cbor2
import pytest
from retry import retry

from pycardano import *

from .base import TEST_RETRIES, TestBase


class TestPlutus(TestBase):
    @retry(tries=TEST_RETRIES, backoff=1.5, delay=3, jitter=(0, 4))
    def test_create_user_stake_transaction(self):
        sys.path.append("../src")

        from lib import script_tools, cardano_types

        sender_address = Address(self.payment_vkey.hash(), network=self.NETWORK)
        nft_symbol = (
            ScriptPubkey(VerificationKey.from_signing_key(self.payment_skey).hash())
            .hash()
            .payload
        )

        # ----------- Mint Script NFT -----------

        tokens_policy = (
            (
                ScriptPubkey(VerificationKey.from_signing_key(self.payment_skey).hash())
                .hash()
                .payload
            ),
        )

        script_tools.mint_nfts(
            self.chain_context,
            self.payment_skey,
            self.payment_skey,
            sender_address,
            {b"mediator": 3, b"target": 2},
        )

        time.sleep(3)

        self.assert_output(
            sender_address,
            TransactionOutput(
                address=sender_address,
                amount=Value.from_primitive(
                    [
                        5_000_000,
                        {nft_symbol: {b"mediator": 3, b"target": 2}},
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
                tokens_policy,
                tokens_policy,
                tokens_policy,
                1691711382000,
            )

            escrow_script = cbor2.loads(bytes.fromhex(script_hex))
            script_hash = plutus_script_hash(PlutusV1Script(escrow_script))
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

        time.sleep(3)

        self.assert_output(
            script_address,
            TransactionOutput(
                address=script_address,
                amount=10_000_000,
                datum_hash=cardano_types.ContractDatum(
                    mediators=tokens_policy,
                    target=tokens_policy,
                    fallback=tokens_policy,
                    deadline=1691711382000,
                ).hash(),
            ),
        )
