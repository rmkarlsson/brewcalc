
from system_profile import Braumeister20Short, PhysicalConstants
from dataclasses import dataclass
from pydantic import TypeAdapter
import yaml

@dataclass(frozen=True)
class TurbidStep:
    temp_c: int
    time_min: int
    percent_water: int  # Procent av total vattenmängd som tillsätts i detta steg


class TurbidMashCalculator:
    WATER_SPECIFIC_HEAT = 4.18
    MALT_SPECIFIC_HEAT = 1.7
    STAINLESS_HEAT = 0.5

    def __init__(self, system: Braumeister20Short):
        self.sys = system

        # Läs YAML-filen
        with open("turbid_steps.yaml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Bygg list[TurbidStep] automatiskt
        adapter = TypeAdapter(list[TurbidStep])
        steps = adapter.validate_python(data["steps"])
        self.steps: List[TurbidStep] = steps

    def calculate(self, total_grain_kg, mash_in_l, ambient_temp_c):
        inital_temp_c = ambient_temp_c
        total_water_l = 0.0
        for step in self.steps:
            # Beräkna mängden vatten som ska tillsättas i detta steg
            water_to_add_l = (step.percent_water / 100.0) * mash_in_l

            temp_diff_c = step.temp_c - inital_temp_c
            inital_temp_c = step.temp_c
            energy_needed_malt_kj = temp_diff_c * (total_grain_kg * self.MALT_SPECIFIC_HEAT +
                                                   total_water_l * self.WATER_SPECIFIC_HEAT +
                                                   self.sys.system_weight_kg * self.STAINLESS_HEAT)  
            water_temp_needed = (energy_needed_malt_kj / (water_to_add_l * self.WATER_SPECIFIC_HEAT)) + inital_temp_c
            total_water_l = water_to_add_l + total_water_l
            if (water_to_add_l > 0):
               print(f"Steg: {step}, Vatten att tillsätta: {water_to_add_l:.2f} L at temp {water_temp_needed:.2f} °C") 
            else:
                print(f"Steg: {step}, Vatten att ta bort: {abs(water_to_add_l):.2f} L")   
        
