import os
import logging
import argparse

from bitterness_calculator import BitternessCalculator
from gravity_calculator import GravityCalculator
from system_profile import Braumeister20Short, PhysicalConstants
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
    # module logger for later debug output
    logger = logging.getLogger(__name__)

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


    gravity_calc.get_volume_loss_from_grain(total_grain_kg)
    spent_gain_volume_loss = gravity_calc.get_volume_loss_from_grain(total_grain_kg)
    logger.debug(f"Volume loss from grain: {spent_gain_volume_loss:.2f} L")

    mash_loss_compensated_volume_l = total_batch_size_l + spent_gain_volume_loss
    grain_bill = gravity_calc.calc_grain_bill(
        target_plato=recipe.data["target_og_plato"],
        batch_size_l=mash_loss_compensated_volume_l,
        malts_percent=recipe.data["mash_fermentables"],
    )
    total_grain_kg = gravity_calc.calc_total_grain_kg(grain_bill)

    boil_off_volume_l = (recipe.data.get("boil_time_min") / PhysicalConstants().minutes_per_h) * system.boil_off_l_per_hour
    mash_in_volume_l = mash_loss_compensated_volume_l  + boil_off_volume_l
    logger.info(f"Mash-in volume needed: {mash_in_volume_l:.2f} L")




    # Log results
    logger = logging.getLogger(__name__)
    logger.info("=== Final grain Bill ===")
    logger.info(f"Batch size: {mash_loss_compensated_volume_l:.1f} L")
    logger.info("Malts:")
    for item in grain_bill:
        logger.info(f"  {item['name']}: {item['amount_kg']:.1f} kg")
    logger.info(f"Total grain: {total_grain_kg:.1f} kg")

    system = Braumeister20Short()

    get_num_mashes = system.get_num_mashes(total_grain_kg)
    logger.info(f"Number of mashes required: {get_num_mashes}")


    bitterness_calc = BitternessCalculator()
    hops_additions = bitterness_calc.calc_hops_additions(
        plato=recipe.data["target_og_plato"],
        volume=total_batch_size_l,
        target_ibu=recipe.data["target_ibu"],
        hops=recipe.data["boil_hops"])

    logger.info("=== Hops Additions ===")
    for hop in hops_additions:
        logger.info(f"  {hop['hop']}: {hop['weight']:.1f} g")
