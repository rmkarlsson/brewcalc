from typing import Tuple, Dict
from system_profile import Braumeister20Short
from system_profile import PhysicalConstants


class MashCalculator:
    """
    Hanterar:
    - enkel- och dubbelmäskning
    - vätskeförluster
    - total vattenmängd som ska tillsättas vid start
    """

    def __init__(self, system: Braumeister20Short):
        self.sys = system

    # -----------------------------
    #   Interna hjälpfunktioner
    # -----------------------------


    def total_water_needed(
        self,
        batch_size_l: float,
        boil_time_min: float,
        total_grain_kg: float
    ) -> Dict[str, float]:
        """
        Allt vatten tillsätts vid start.
        Beräknar:
        - mäskförluster (enkel/dubbel)
        - kokförlust
        - trubförlust
        - total vattenmängd som ska tillsättas
        """
        if total_grain_kg <= 0:
            raise ValueError("Total maltmängd måste vara > 0 kg.")

        boil_off = (boil_time_min / PhysicalConstants().minutes_per_h) * self.sys.boil_off_l_per_hour
        first, second, mash_losses = self.double_mash_losses(total_grain_kg)

        total_water = batch_size_l + boil_loss + self.sys.trub_loss_l + mash_losses

        if total_water < self.sys.min_mash_volume_l:
            raise ValueError(
                f"Beräknad total vattenmängd ({total_water:.2f} L) "
                f"är mindre än systemets minsta praktiska volym "
                f"({self.sys.min_mash_volume_l:.2f} L)."
            )

        return {
            "grain_total_kg": total_grain_kg,
            "first_mash_grain_kg": first,
            "second_mash_grain_kg": second,
            "mash_losses_l": mash_losses,
            "boil_loss_l": boil_loss,
            "trub_loss_l": self.sys.trub_loss_l,
            "total_water_l": total_water,
        }

    @staticmethod
    def pretty(plan: Dict[str, float]) -> None:
        print("=== Dubbelmäskningsplan (BM20 kort maltpipa) ===")
        print(f"Total malt:           {plan['grain_total_kg']:.2f} kg")
        print(f"Första mäskningen:    {plan['first_mash_grain_kg']:.2f} kg")
        print(f"Andra mäskningen:     {plan['second_mash_grain_kg']:.2f} kg")
        print(f"Mäskförluster:        {plan['mash_losses_l']:.2f} L")
        print(f"Kokförlust:           {plan['boil_loss_l']:.2f} L")
        print(f"Trubförlust:          {plan['trub_loss_l']:.2f} L")
        print(f"Total vattenmängd in: {plan['total_water_l']:.2f} L")