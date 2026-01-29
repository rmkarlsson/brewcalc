import os
import logging
import argparse

from gravity_calculator import GravityCalculator
from system_profile import Braumeister20Short
from recipe_loader import RecipeLoader


if __name__ == "__main__":
    # CLI and global logging config
    parser = argparse.ArgumentParser(description="Brecac kalkylator")
    parser.add_argument(
        "-d",
        "--debug_level",
        help="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        type=str.upper,
        default=None,
    )
    args = parser.parse_args()

    # Determine log level: CLI arg overrides env var
    log_level = args.debug_level
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger(__name__).info("Starting brecalc (log_level=%s)", log_level)

    # 1. Läs recept
    recipe = RecipeLoader("recipe.yaml")

    # 2. Initiera system och kalkylatorer
    system = Braumeister20Short()

    gravity_calc = GravityCalculator(system)
    total_batch_size_l = recipe.data["batch_size_l"] + system.trub_loss_l
    grain_bill = gravity_calc.calc_grain_bill(
        target_plato=recipe.data["target_og_plato"],
        batch_size_l=total_batch_size_l,
        malts_percent=recipe.data["mash_fermentables"],
    )
    total_grain_kg = gravity_calc.calc_total_grain_kg(grain_bill)

    # Log results
    logger = logging.getLogger(__name__)
    logger.debug("=== Grain Bill estimated ===")
    logger.debug(f"Batch size: {recipe.data['batch_size_l']} L")
    logger.debug("Malts:")
    for item in grain_bill:
        logger.debug(f"  {item['name']}: {item['amount_kg']:.2f} kg")
    logger.debug(f"Total grain: {total_grain_kg:.2f} kg")



    gravity_calc.get_volume_loss_from_grain(total_grain_kg)
    volume_loss = gravity_calc.get_volume_loss_from_grain(total_grain_kg)
    logger.debug(f"Volume loss from grain: {volume_loss:.2f} L")

    mash_loss_compensated_volume_l = total_batch_size_l + volume_loss
    grain_bill = gravity_calc.calc_grain_bill(
        target_plato=recipe.data["target_og_plato"],
        batch_size_l=mash_loss_compensated_volume_l,
        malts_percent=recipe.data["mash_fermentables"],
    )
    total_grain_kg = gravity_calc.calc_total_grain_kg(grain_bill)

    # Log results
    logger = logging.getLogger(__name__)
    logger.debug("=== Grain Bill mash loss compensated ===")
    logger.debug(f"Batch size: {recipe.data['batch_size_l']} L")
    logger.debug("Malts:")
    for item in grain_bill:
        logger.debug(f"  {item['name']}: {item['amount_kg']:.2f} kg")
    logger.debug(f"Total grain: {total_grain_kg:.2f} kg")

    system = Braumeister20Short()

    get_num_mashes = system.get_num_mashes(total_grain_kg)
    logger.debug(f"Number of mashes required: {get_num_mashes}")

