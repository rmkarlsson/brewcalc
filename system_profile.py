from dataclasses import dataclass


@dataclass
class Braumeister20:
    """
    Systemprofil för Braumeister 20L med kort maltpipa.
    Alla värden är empiriska / typiska och kan justeras.
    """
    min_mash_volume_l: float = 10.0       # praktisk minsta vätskemängd i kärlet
    max_grain_per_mash_kg: float = 5.0    # max malt i kort maltpipa
    boil_off_l_per_hour: float = 3.0      # kokförlust per timme
    trub_loss_l: float = 1.2              # kon + humle + dödutrymme
    mash_efficiency: float = 0.8
    boiler_diameter_mm: float = 348          # diameter på kokkärl
    system_weight_kg: float = 15.0                # vikt på systemet (kg), används för att beräkna energibehov

    def get_volume_in_mm(self, volume_l: float) -> float:
        """
        Returnerar höjd i mm per liter vätska i kokkärlet.
        Används för att beräkna vätskestånd vid mäskning och kok.
        """
        radius_mm = self.boiler_diameter_mm / 2
        area_mm2 = 3.1416 * (radius_mm ** 2)
        mm_per_liter = 1_000_000 / area_mm2  # 1 liter = 1 000 000 mm³

        return mm_per_liter * volume_l


    def get_volume_l(into_mm: int) -> float:
        """
        Returnerar volym i liter baserat på höjd i mm i kokkärlet.
        """
        radius_mm = self.boiler_diameter_mm / 2
        area_mm2 = 3.1416 * (radius_mm ** 2)
        volume_mm3 = area_mm2 * into_mm
        volume_l = volume_mm3 / 1_000_000  # 1 liter = 1 000 000 mm³
        return volume_l

    def get_num_mashes(self, total_grain_kg: float) -> int:
        """
        Returnerar antal mashar baserat på maltmängd och max malt per mash.
        """
        from math import ceil
        return ceil(total_grain_kg / self.max_grain_per_mash_kg)


@dataclass
class Braumeister20Short(Braumeister20):
    """
    Systemprofil för Braumeister 20L med normal (stor) maltpipa.
    Samma fält som `Braumeister20Short` men med högre `max_grain_per_mash_kg`.
    """
    # Ärver fält och metoder från Braumeister20Short, bara överskriv max_grain_per_mash_kg
    max_grain_per_mash_kg: float = 2.6

@dataclass
class PhysicalConstants:
    """
    Fysiska konstanter som kan återanvändas i olika moduler.
    """
    # Modulkonstant: volym (L) absorberad per kg malt
    grain_obsortion_l_kg: float = 0.8
    minutes_per_h: float = 60.0


