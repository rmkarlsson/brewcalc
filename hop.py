from dataclasses import dataclass
from enum import Enum


class HopType(Enum):
    CONE = "cone"
    WHOLE = "whole"
    CONCENTRATE = "concentrate"


@dataclass
class Hop:
    name: str
    alpha_acid: float
    hop_type: HopType
    amount_g: float = 0.0 
    effective_steep_time: float = 0.0
    comment: str = ""

    def __init__(self, name: str, alpha_acid: float, hop_type: HopType):
        self.name = name
        self.alpha_acid = alpha_acid
        self.hop_type = hop_type
