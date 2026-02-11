from dataclasses import dataclass
import string
from rich.console import Console
from rich.table import Table
from rich.panel import Panel


@dataclass
class Malt:
    """
    Representerar volymerna före och efter kok.
    """
    name: string
    amount_kg: float  # Volym innan kok (L)
    percent: float  # Volym innan kok (L)
    color_ecb: float  # Volym efter kok (L)
    extract: float  # Volymförlust i mäskning (L)

    def __init__(self, name: string, extract: float, percent: float, color_ecb: float):
        self.color_ecb = color_ecb
        self.percent = percent
        self.extract = extract
        self.name = name
        self.amount_kg = 0.0