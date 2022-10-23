from dataclasses import dataclass
from pycardano import PlutusData


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