from dataclasses import dataclass
from pycardano import PlutusData


@dataclass
class ContractDatum(PlutusData):
    CONSTR_ID = 0
    target: bytes
    fallback: bytes
    mediatorsNFT: bytes
    deadline: int


@dataclass
class SendToTarget(PlutusData):
    CONSTR_ID = 0


@dataclass
class SendToFallback(PlutusData):
    CONSTR_ID = 1
    mediator: bytes
    reference_input_index: int