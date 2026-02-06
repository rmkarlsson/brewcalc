from typing import Dict, List
import logging
from malts_db import get_malt
from system_profile import Braumeister20Short, PhysicalConstants
import copy

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

    def calc_total_grain_kg(self, grain_bill: List[Dict]) -> float:
        return sum(m["amount_kg"] for m in grain_bill) 


    def get_pre_boil_plato(self, malts: List[Dict], og_plato: float):
        percent = 0
        for m in malts:
            malt_info = get_malt(m["name"])
            percent = percent + (m["percent"] / 100.0)
        return percent * og_plato


    def calc_grain_bill(
        self,
        target_plato: float,
        batch_size_l: float,
        malts_percent: List[Dict]
    ) -> List[Dict]:
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
            len(malts_percent),
        )

        # Total extraktmängd i Plato-liter
        total_extract = target_plato * batch_size_l / 100.0

        result = []
        total_grain_kg = 0.0

        for m in malts_percent:
            malt_info = get_malt(m["name"])
            percent_fermentable = m["percent"] / 100.0
            extract_percent = malt_info["extract_percent"]

            # Extrakt som denna malt ska bidra med
            extract_i = total_extract * percent_fermentable

            # kg malt som krävs
            grain_kg_i = extract_i / (extract_percent * self.sys.mash_efficiency)

            m_with_grain_weight = copy.deepcopy(malt_info)
            # Add amount_kg to dict
            m_with_grain_weight["amount_kg"] = grain_kg_i
            m_with_grain_weight["name"] = m["name"]

            logger.debug("Adding malt: %s", m_with_grain_weight)
            logger.debug("Adding og-malt: %s", malt_info)

            result.append(m_with_grain_weight)

            total_grain_kg += grain_kg_i

        return result