from typeguard import typechecked
from typing import Union
from pycardano import *
from blockfrost import ApiError
from retry import retry
from dataclasses import dataclass

import cbor2


# A future improvement to make this fast would be to use a private network with no tx delays


@typechecked
class ScriptTester:
    """Interfaces through which user can create script off-chain tests"""

    def __init__(
        self,
        blockfrost_id: str,
        network: Network,
        script_path: str,
        skey_path: str,
        sender_address: str,
    ):
        self._blockfrost_id = blockfrost_id
        self._network = network

        self._chain_context = BlockFrostChainContext(
            project_id=self._blockfrost_id,
            network=self._network,
            base_url=(
                "https://cardano-mainnet.blockfrost.io/api"
                if network == Network.MAINNET
                else "https://cardano-preview.blockfrost.io/api"
            )
        )

        self._skey = PaymentSigningKey.load(skey_path)

        with open(script_path, "r") as f:
            script_hex = f.read()

        self._script = cbor2.loads(bytes.fromhex(script_hex))

        self._script_address = Address(
            plutus_script_hash(PlutusV2Script(self._script)), network=self._network
        )
        self._sender_address = Address.from_primitive(sender_address)

    @retry(delay=20)
    def _wait_for_tx(self, tx_id: str):
        self._chain_context.api.transaction(tx_id)
        print(
            f"Transaction {tx_id} has been successfully included in the blockchain.")

    def _find_collateral(self, target_address: Address) -> Union[UTxO, None]:
        for utxo in self._chain_context.utxos(str(target_address)):
            # A collateral should contain no multi asset
            if not utxo.output.amount.multi_asset:
                return utxo

        return None

    def _create_collateral(self, target_address: Address, skey: PaymentSigningKey):
        collateral_builder = TransactionBuilder(self._chain_context)

        collateral_builder.add_input_address(target_address)
        collateral_builder.add_output(
            TransactionOutput(target_address, 5_000_000))

        self._submit_tx(collateral_builder.build_and_sign(
            [skey], target_address))

    def _submit_tx(self, tx: Transaction):
        print("############### Transaction created ###############")
        print(tx)
        print(tx.to_cbor())
        print("############### Submitting transaction ###############")

        self._chain_context.submit_tx(tx.to_cbor())
        self._wait_for_tx(str(tx.id))

    def script_exists(
        self,
        amount: Union[int, Value],
        datum: Datum,
    ) -> Union[UTxO, None]:
        try:
            utxos = self._chain_context.utxos(str(self._script_address))
        except ApiError as err:
            if err.status_code == 404:
                return None
            else:
                raise err

        return next(
            filter(
                lambda utxo: utxo.output.amount == amount
                and utxo.output.datum_hash == datum_hash(datum),
                utxos,
            ),
            None,
        )

    def submit_script(self, amount: Union[int, Value], datum: Datum) -> UTxO:
        """Submits script to the chain if it's not already there
        Args:
            amount (Value): The value we are sending to this script (or making sure is already there)
            datum (Datum): The datum we are attaching to the script (or making sure it already there)
        Returns:
            UTxO: The newly formed UTxO (if there wasn't one already there)
        Raises:
            :class:`FileNotFoundError`: When the files for the secret key or script can't be found.
        """

        # If there already is a script with the info provided, return it
        utxo = self.script_exists(amount, datum)

        if utxo is not None:
            return utxo

        builder = TransactionBuilder(self._chain_context)
        builder.add_input_address(self._sender_address)
        builder.add_output(
            TransactionOutput(self._script_address, amount,
                              datum_hash=datum_hash(datum)),
            datum=datum,
            add_datum_to_witness=True,
        )

        signed_tx = builder.build_and_sign([self._skey], self._sender_address)

        script_output_index = None
        for index in range(len(signed_tx.transaction_body.outputs)):
            if signed_tx.transaction_body.outputs[index].datum_hash is not None:
                script_output_index = index
                break

        if script_output_index is None:
            # This should never happen
            raise Exception("Malformed transaction body, no script found!")

        self._submit_tx(signed_tx)

        return UTxO(
            TransactionInput(signed_tx.id, script_output_index),
            TransactionOutput(self._script_address, amount,
                              datum_hash=datum_hash(datum)),
        )

    def transaction_builder(self, utxo: UTxO, datum: Datum) -> Transaction:
        """Builds a transaction given a script UTxO
        Args:
            utxo (UTxO): The UTxO of the script we are consuming in this transaction
            datum (Datum): The datum of the transaction we are building
        Returns:
            Transaction: The transaction we built for consuming the given script
        Raises:
            :class:`FileNotFoundError`: When the file for the secret key can't be found.
        """
        raise NotImplementedError()

    def validate_transaction(self, utxo: UTxO, datum: Datum) -> bool:
        """Tries to evaluate the transaction and returns whether it would succeed or not
        Args:
            utxo (UTxO): The UTxO of the script we are consuming in this transaction
            datum (Datum): The datum of the transaction we are building
        Returns:
            bool: Whether the given transaction would succeed or not
        Raises:
            :class:`FileNotFoundError`: When the file for the secret key can't be found.
        """

        try:
            self.transaction_builder(utxo, datum)
            return True
        except TransactionFailedException as e:
            print(e)
            return False


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

random_policy = bytes.fromhex(
    "65783e84e04af28ecb157abc4d18bb12728d2326c5afd69302077de9")


@dataclass
class ContractDatum(PlutusData):
    CONSTR_ID = 0
    mediators: bytes
    target: bytes
    fallback: bytes
    deadline: int


@dataclass
class ExecuteTarget(PlutusData):
    CONSTR_ID = 0


@dataclass
class ExecuteFallback(PlutusData):
    CONSTR_ID = 1


class ScriptTesterTarget(ScriptTester):

    def transaction_builder(self, utxo: UTxO, datum: Datum) -> Transaction:
        redeemer = Redeemer(RedeemerTag.SPEND, ExecuteTarget())

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
        builder.add_input_address(bob_address)

        alice_utxos = self._chain_context.utxos(str(alice_address))

        alice_utxo = None
        for utxo in alice_utxos:
            if utxo.output.amount.multi_asset:
                if ScriptHash.from_primitive(target_policy) in utxo.output.amount.multi_asset:
                    alice_utxo = utxo

        if alice_utxo is None:
            raise Exception(
                f"Could not find UTxO with token in address {str(alice_address)}")

        builder.reference_inputs.add(alice_utxo.input)

        take_output = TransactionOutput(alice_address, 5_149_265)

        builder.add_output(take_output)

        signed_tx = builder.build_and_sign([bob_skey], bob_address)

        return signed_tx


class ScriptTesterTargetNoToken(ScriptTester):

    def transaction_builder(self, utxo: UTxO, datum: Datum) -> Transaction:
        redeemer = Redeemer(RedeemerTag.SPEND, ExecuteTarget())

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
        builder.add_input_address(bob_address)

        alice_utxos = self._chain_context.utxos(str(alice_address))

        alice_utxo = None
        for utxo in alice_utxos:
            if utxo.output.amount.multi_asset:
                if ScriptHash.from_primitive(target_policy) in utxo.output.amount.multi_asset:
                    alice_utxo = utxo

        if alice_utxo is None:
            raise Exception(
                f"Could not find UTxO with token in address {str(alice_address)}")

        take_output = TransactionOutput(alice_address, 5_149_265)

        builder.add_output(take_output)

        signed_tx = builder.build_and_sign([bob_skey], bob_address)

        return signed_tx


class ScriptTesterTargetWrongToken(ScriptTester):

    def transaction_builder(self, utxo: UTxO, datum: Datum) -> Transaction:
        redeemer = Redeemer(RedeemerTag.SPEND, ExecuteTarget())

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
        builder.add_input_address(bob_address)

        alice_utxos = self._chain_context.utxos(str(alice_address))

        random_policy = "65783e84e04af28ecb157abc4d18bb12728d2326c5afd69302077de9"

        alice_utxo = None
        for utxo in alice_utxos:
            if utxo.output.amount.multi_asset:
                if ScriptHash.from_primitive(random_policy) in utxo.output.amount.multi_asset and ScriptHash.from_primitive(target_policy) not in utxo.output.amount.multi_asset:
                    alice_utxo = utxo

        print(alice_utxo)

        if alice_utxo is None:
            raise Exception(
                f"Could not find UTxO with token in address {str(alice_address)}")

        builder.reference_inputs.add(alice_utxo.input)

        take_output = TransactionOutput(alice_address, 5_149_265)

        builder.add_output(take_output)

        signed_tx = builder.build_and_sign([bob_skey], bob_address)

        return signed_tx
