import time
import sys
import cbor2
import pytest
from retry import retry

from pycardano import *

from .base import TEST_RETRIES, TestBase


class TestPlutus(TestBase):

    @retry(tries=TEST_RETRIES, backoff=1.5, delay=6, jitter=(0, 4))
    def test_create_user_stake_transaction(self):
        sys.path.append("../src")

        from lib import script_tools

        sender_address = Address(self.payment_vkey.hash(), network=self.NETWORK)
        nft_symbol = (
            ScriptPubkey(VerificationKey.from_signing_key(self.payment_skey).hash())
            .hash()
            .payload
        )

        # ----------- Mint Script NFT -----------

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
                        3_000_000,
                        {nft_symbol: {b"mediator": 3, b"target": 2}},
                    ]
                ),
            ),
        )

        # ----------- Giver give ---------------

        # with open("../script/script.plutus", "r") as f:
        #     script_hex = f.read()

        #     transaction = cardano_utils.create_user_stake_transaction(
        #         self.chain_context,
        #         sender_address,
        #         script_hex,
        #         ScriptPubkey(VerificationKey.from_signing_key(self.payment_skey).hash())
        #         .hash()
        #         .payload.hex(),
        #     )

        #     gero_script = cbor2.loads(bytes.fromhex(script_hex))
        #     script_hash = plutus_script_hash(PlutusV1Script(gero_script))
        #     script_address = Address(script_hash, network=self.NETWORK)

        # # ----------- Submit Transaction --------------

        # # Sign the transaction body hash
        # signature = self.payment_skey.sign(transaction.transaction_body.hash())

        # # Add verification key and the signature to the witness set
        # vk_witnesses = [VerificationKeyWitness(self.payment_vkey, signature)]

        # transaction.transaction_witness_set = TransactionWitnessSet(
        #     vkey_witnesses=vk_witnesses
        # )

        # signed_tx = Transaction(
        #     transaction.transaction_body,
        #     TransactionWitnessSet(vkey_witnesses=vk_witnesses),
        # )

        # self.chain_context.submit_tx(signed_tx.to_cbor())

        # time.sleep(3)

        # self.assert_output(
        #     script_address,
        #     TransactionOutput(
        #         address=script_address,
        #         amount=Value.from_primitive(
        #             [
        #                 3_000_000,
        #                 {nft_symbol: {b"us-0": 1}},
        #             ]
        #         ),
        #         datum_hash=cardano_types.UserStakeDetail(
        #             user_pkh=sender_address.payment_part.payload,
        #             votes={},
        #             delegated_to=sender_address.payment_part.payload,
        #             index=0,
        #             sym=nft_symbol,
        #         ).hash(),
        #     ),
        # )