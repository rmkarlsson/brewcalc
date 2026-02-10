import math
from typing import Dict, List
import logging
import copy
from hops_db import get_hop
from system_profile import PhysicalConstants
from gravity_calculator import GravityCalculator

# Module logger
logger = logging.getLogger(__name__)


class BitternessCalculator:

    def __init__(self):
        pass

    def calc_hops_additions(self, plato: float, volume: float, target_ibu: float, hops: list[Dict]) -> list[Dict]:
        # Calculate hop additions based on malt percentages and volume

        hops_additions = []
        for hop in hops:
            # Hämta humleinfo från hops_db
            try:
                hop_info = get_hop(hop['name'])
            except ValueError:
                logger.error("Humlesort saknas i databasen: %s", hop['name'])
                raise

            alpha_acid = hop_info.get('alpha_acid')
            if alpha_acid is None:
                logger.error("'alpha_acid' saknas för humlesort: %s", hop['name'])
                raise ValueError(f"'alpha_acid' saknas för humlesort: {hop['name']}")

            boil_time = hop.get('boil_time_min')
            if boil_time is None:
                logger.error("'boil_time_min' saknas för humlesort i receptet: %s", hop['name'])
                raise ValueError(f"'boil_time_min' saknas för humlesort i receptet: {hop['name']}")

            logger.debug("Hop IBU contribution in percent: %s, target_ibu %s, alpha_acid %s, boil time %s", hop['percent'],  target_ibu, alpha_acid, boil_time)
            grams = self.hop_weight_grams((hop['percent']/100) * target_ibu, volume, plato, boil_time, alpha_acid)

            logger.debug(
                "Hop calc: name=%s percent=%s boil_time_min=%s alpha_acid=%.3f grams=%.2f",
                hop['name'], hop.get('percent'), boil_time, alpha_acid, grams,
            )
            
            # Use hops_db as base and add weight from calulation and and boil time from receipe
            hops_addition = copy.deepcopy(hop_info)
            hops_addition['name'] = hop['name'] 
            hops_addition['weight'] = grams
            hops_addition['boil_time_min'] = hop['boil_time_min']

            hops_additions.append(hops_addition)

        return hops_additions



    def tinseth_utilization(self, plato: float, boil_time_min: float) -> float:
        og = GravityCalculator.plato_to_og(plato)
        f_og = 1.65 * math.pow(0.000125, (og - 1.0))
        f_t = (1 - math.exp(-0.04 * boil_time_min)) / 4.15
        logger.debug("tinseth utilization: plato %.2f, og %.3f, boil_time_min=%.1f, utilization=%.3f", plato, og, boil_time_min, f_og * f_t)
        return f_og * f_t

    def hop_weight_grams(self, target_ibu: float, volume_l: float,
                     plato: float, boil_time_min: float,
                     alpha_acid: float) -> float:
        U = self.tinseth_utilization(plato, boil_time_min)
        ibu = (target_ibu * volume_l) / (1000 * alpha_acid * U)
        logger.debug("Calculated hop weight grams: target_ibu=%.1f, volume_l=%.1f, plato=%.1f, boil_time_min=%.1f, alpha_acid=%.3f => grams=%.2f",
                     target_ibu, volume_l, plato, boil_time_min, alpha_acid, ibu)
        return ibu