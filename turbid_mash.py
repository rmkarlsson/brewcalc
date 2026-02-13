
from system_profile import Braumeister20Short, PhysicalConstants
from dataclasses import dataclass
from pydantic import TypeAdapter
import yaml

@dataclass(frozen=True)
class TurbidStep:
    target_temp_c: float
    time_min: float
    percent_water: float  # Procent av total vattenmängd som tillsätts i detta steg

class TurbidMashStep(TurbidStep):
    water_l: float = 0.0     
    water_temp_c: float = 0.0

    def __init__(self, target_temp_c: float, time_min: float, water_temp_c: float, water_l: float):
        super().__init__(target_temp_c, time_min, percent_water=0.0)  # percent_water används inte i denna klass
        self.water_l = water_l
        self.water_temp_c = water_temp_c

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
        self.steps: list[TurbidStep] = steps

    def calculate(self, total_grain_kg, mash_in_l, ambient_temp_c) -> list[TurbidMashStep]:
        inital_temp_c = ambient_temp_c
        total_water_l = 0.0
        water_to_add_l = 0.0
        result = []
        for step in self.steps:
            if step.percent_water < 0:
                # When removing water use current mash vloume and not total mash_in volume
                water_to_add_l = (step.percent_water / 100.0) * total_water_l
                energy_needed_malt_kj = 0.0
                temp_diff_c = 0.0
                water_temp_needed = step.target_temp_c
            else:
                # When adding water, use the total mash_in_l
                water_to_add_l = (step.percent_water / 100.0) * mash_in_l
              
                temp_diff_c = step.target_temp_c - inital_temp_c
                inital_temp_c = step.target_temp_c
                energy_needed_malt_kj = temp_diff_c * (total_grain_kg * self.MALT_SPECIFIC_HEAT +
                                                    total_water_l * self.WATER_SPECIFIC_HEAT +
                                                    self.sys.system_weight_kg * self.STAINLESS_HEAT)  
                water_temp_needed = (energy_needed_malt_kj / (water_to_add_l * self.WATER_SPECIFIC_HEAT)) + inital_temp_c
            total_water_l = water_to_add_l + total_water_l

                
            result.append(TurbidMashStep(
                target_temp_c=step.target_temp_c,      
                time_min=step.time_min,
                water_temp_c=water_temp_needed,
                water_l=water_to_add_l))

        
        return result