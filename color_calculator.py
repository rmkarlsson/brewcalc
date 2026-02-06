import math
import string
from typing import List, Dict


class ColorCalculator:
    """
    Beräknar färg i EBC med Morey-formeln.
    Kräver:
    - lista av mash_fermentables med 'amount_kg' och 'color_ebc'
    - batchvolym i liter
    """
    @staticmethod
    def get_string(color: float) -> string:
        if color <= 5:
            return "Ljust/Gult"
        if color <= 10:
            return "Guld/Bärnsten"
        if color <= 20:
            return "Bärnsten/Koppar"
        if color <= 40:
            return "Koppar/Ljusbrunt"
        if color <= 80:
            return "Mörkbrunt"
        else:
            return "Svart"

    @staticmethod
    def calc_mcu(malts: List[Dict], volume_l: float) -> float:
        """
        MCU = (sum(malt_kg * malt_color_EBC)) / volume_l
        """
        total_mcu = 0.0
        for m in malts:
            kg = m["amount_kg"]
            color = m["color_ebc"]
            total_mcu += kg * color

        return (total_mcu / volume_l)

    @staticmethod
    def calc_ebc_morey(malts: List[Dict], volume_l: float) -> float:
        """
        Morey EBC = 2.9396 * MCU^0.6859
        """
        mcu = ColorCalculator.calc_mcu(malts, volume_l)
        if mcu <= 0:
            return 0.0
        return 7.88 * (mcu ** 0.6859)

    @staticmethod
    def calculate(malts: List[Dict], volume_l: float) -> Dict[str, float]:
        """
        Returnerar både MCU och EBC i ett paket.
        """
        mcu = ColorCalculator.calc_mcu(malts, volume_l)
        ebc = ColorCalculator.calc_ebc_morey(malts, volume_l)

        return {
            "mcu": mcu,
            "ebc": ebc
        }