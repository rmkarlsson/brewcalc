from typing import Dict, List
import logging
from malts_db import get_malt
from system_profile import Braumeister20Short, PhysicalConstants
import copy
from malt import Malt

# Module logger
logger = logging.getLogger(__name__)


class GravityCalculator:
    """
    Räknar ut:
    - preboil-volym
    - kg per malt baserat på extraktprocent och procentandel
    - total maltmängd
    """

    def __init__(self, sys: Braumeister20Short):
        self.sys = sys

    @staticmethod
    def plato_to_og(plato: float) -> float:
        og = 1 + (plato / (258.6 - ((plato / 258.2) * 227.1)))
        logger.debug("Converted plato %.2f to og %.3f", plato, og)
        return og

    def get_volume_loss_from_grain(self, total_grain_kg: float) -> float:
        """
        Returnerar volymförlust (L) baserat på maltmängd (kg)
        """
        # Volymförlust beräknas som maltmängd gånger absorption per kg
        return float(total_grain_kg) * float(PhysicalConstants().grain_obsortion_l_kg)

    def calc_total_grain_kg(self, grain_bill: list[Malt]) -> float:
        return sum(m.amount_kg for m in grain_bill) 


    def get_pre_boil_plato(self, malts: list[Malt], og_plato: float):
        percent = 0
        for m in malts:
            malt_info = get_malt(m["name"])
            percent = percent + (m["percent"] / 100.0)
        return percent * og_plato


    def calc_grain_bill(
        self,
        target_plato: float,
        batch_size_l: float,
        grain_bill: list[Malt]
    ):
        """
        Returnerar en lista med:
        - name
        - percent
        - extract_percent
        - amount_kg
        """

        

        logger.debug(
            "calc_grain_bill: target_plato=%.1f, batch_size_l=%.1f, malts_count=%d",
            target_plato,
            batch_size_l,
            len(grain_bill),
        )

        # Total extraktmängd i Plato-liter
        total_extract = target_plato * batch_size_l / 100.0

        for m in grain_bill:
            # Extrakt som denna malt ska bidra med
            extract = total_extract * m.percent

            # kg malt som krävs
            m.amount_kg = extract / (m.extract * self.sys.mash_efficiency)

            logger.debug("Adding malt: %s", m.amount_kg)