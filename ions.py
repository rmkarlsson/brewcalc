from venv import logger

from pydantic import BaseModel

from recipe import Ion

'''1 g per 10 l ger tillskott av 27,6 mg/l Ca2+ och 66,2 mg/l SO42-'''
'''1 gram per 10 liter ger ett tillskott av 27,8 mg/l Kalcium (Ca2+) och 49,2 mg/l klorid (Cl-).'''
SALT_DB = {
    "Calcium chloride": {
        "Calcium": 28,
        "Chloride": 49
    },
    "Calcium sulfate": {
        "Calcium": 27,
        "Sulfate": 67
    }
}

WATER_ION_DB = {
    "Calcium": {
        "content_mg_per_l": 17
    },
    "Chloride": {
        "content_mg_per_l": 6.8
    },
    "Sulfate": {
        "content_mg_per_l": 9.4
    }
}

class ion_estimator:
    def __init__(self, salt_db: dict[str, dict[str, float]]):
        self.salt_db = SALT_DB
    
    @staticmethod
    def estimate_salt_amount(ion: Ion, volume_post_liters: float, volume_mash_loss: float) -> float:
        if ion.salt_name not in SALT_DB:
            raise ValueError(f"Salt '{ion.salt_name}' not found in database.")
        
        salt_composition = SALT_DB[ion.salt_name]
        ion_to_add_mg_per_l = ion.amount_mg_per_l - WATER_ION_DB.get(ion.name, {}).get("content_mg_per_l", 0)
        logger.info(f"Current {ion.name} content is {WATER_ION_DB.get(ion.name, {}).get('content_mg_per_l', 0)} mg/L, need to add {ion_to_add_mg_per_l} mg/L to reach target of {ion.amount_mg_per_l} mg/L.")
        if ion_to_add_mg_per_l <= 0:
            logger.info(f"No additional {ion.name} needed, current content is sufficient.")
            return 0
        ion_to_add_grams = (ion_to_add_mg_per_l * (volume_post_liters + volume_mash_loss)) / 1000
        logger.info(f"Total {ion.name} to add: {ion_to_add_grams:.2f} grams for {volume_post_liters:.2f} liters post-boil and {volume_mash_loss:.2f} liters mash loss.")
        if ion.name not in salt_composition:
            raise ValueError(f"Ion '{ion.name}' not found in salt '{salt_composition}'.")
        salt_to_add_grams = ion_to_add_grams / (salt_composition.get(ion.name, 0) / 100)
        logger.info(f"Estimated salt amount to add: {salt_to_add_grams:.2f} grams.")
        return salt_to_add_grams
