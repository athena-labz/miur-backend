from typeguard import typechecked
from typing import Union
from pycardano import *
from blockfrost import ApiError
from retry import retry

import cbor2


# A future improvement to make this fast would be to use a private network with no tx delays


@typechecked
class ScriptTester:
    """Interfaces through which user can create script off-chain tests"""

    def __init__(
        self,
        blockfrost_id: str,
        network: Network,
        skey_path: str,
        script_path: str,
        sender_address: str,
    ):
        self._blockfrost_id = blockfrost_id
        self._network = network

        self._chain_context = BlockFrostChainContext(
            project_id=self._blockfrost_id, network=self._network
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
        print(f"Transaction {tx_id} has been successfully included in the blockchain.")

    def _find_collateral(self, target_address: Address) -> Union[UTxO, None]:
        for utxo in self._chain_context.utxos(str(target_address)):
            # A collateral should contain no multi asset
            if not utxo.output.amount.multi_asset:
                return utxo

        return None

    def _create_collateral(self, target_address: Address, skey: PaymentSigningKey):
        collateral_builder = TransactionBuilder(self._chain_context)

        collateral_builder.add_input_address(target_address)
        collateral_builder.add_output(TransactionOutput(target_address, 5_000_000))

        self._submit_tx(collateral_builder.build_and_sign([skey], target_address))

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
            TransactionOutput(self._script_address, amount, datum_hash=datum_hash(datum)),
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
            TransactionOutput(self._script_address, amount, datum_hash=datum_hash(datum)),
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