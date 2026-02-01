import os
import logging
import argparse
import sys

try:
    from tabulate import tabulate
    HAVE_TABULATE = True
except Exception:
    HAVE_TABULATE = False

from bitterness_calculator import BitternessCalculator
from gravity_calculator import GravityCalculator
from system_profile import Braumeister20Short, PhysicalConstants
from recipe_loader import RecipeLoader
from color_calculator import ColorCalculator


def print_hops_table(hops_additions):
    """Print a simple text table of hop additions. Uses tabulate if available."""
    if HAVE_TABULATE:
        rows = []
        for h in hops_additions:
            rows.append([
                h['name'],
                f"{h['weight']:.1f}",
                f"{h['boil_time_min']}",
                f"{h ['alpha_acid']:.3f}",
            ])
        print(tabulate(rows, headers=["Hop","Weight (g)","Boil time (min)","Alpha acid"], tablefmt="github"))
    else:
        for h in hops_additions:
            print(f"  {h['name']}: {h['weight']:.1f} g (boil_time={h.get('boil_time_min','')} min, alpha_acid={h.get('alpha_acid',0):.3f})")


if __name__ == "__main__":
    # CLI and global logging config
    parser = argparse.ArgumentParser(description="Brecac kalkylator", add_help=False)
    parser.add_argument(
        "-d",
        "--debug_level",
        help="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        type=str.upper,
        default=None,
    )

    # Custom help (we disabled default -h) and hop boil calc
    parser.add_argument("-h", "--help", action="help", default=argparse.SUPPRESS, help="Visa hjälp")
    parser.add_argument("--hop_boil_calc", "-b", action="store_true", help="Aktivera humlekalkyl (kräver --plato/-p och --volume/-v)")
    parser.add_argument("--plato", "-p", type=float, help="Plato (°P) att använda vid humlekalkyl")
    parser.add_argument("--volume", "-v", type=float, help="Volym i liter (L) att använda vid humlekalkyl")

    args = parser.parse_args()

    # Determine log level: CLI arg overrides env var
    log_level = args.debug_level
    effective_level = log_level or "INFO"
    logging.basicConfig(
        level=getattr(logging, effective_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger(__name__).info("Starting brecalc (log_level=%s)", effective_level)
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


    color = ColorCalculator.calculate(
        malts=grain_bill,          # grain_bill innehåller amount_kg och color_ebc
        volume_l=recipe.batch_size_l
    )

    print("MCU:", color["mcu"])
    print("EBC (Morey):", color["ebc"])


    # Om hop_boil_calc anges, kör kalkyl och avsluta
    if args.hop_boil_calc:
        # Validera att båda obligatoriska argumenten finns
        if args.plato is None or args.volume is None:
            parser.error("När --hop_boil_calc/-h anges måste --plato/-p och --volume/-v anges")
        plato_arg = args.plato
        volume_arg = args.volume
        logger.info("Running hop boil calc: plato=%s, volume=%s L", plato_arg, volume_arg)
        bitterness_calc = BitternessCalculator()
        hops_additions = bitterness_calc.calc_hops_additions(
            plato=plato_arg,
            volume=volume_arg,
            target_ibu=recipe.data.get("target_ibu", 0),
            hops=recipe.data.get("boil_hops", []),
        )
        print("=== Hops Additions ===")
        print_hops_table(hops_additions)
        sys.exit(0)
    else:
        # Kör normal kalkyl
        logger.info("Running full brewcalc")
        bitterness_calc = BitternessCalculator()
        hops_additions = bitterness_calc.calc_hops_additions(
            plato=recipe.data["target_og_plato"],
            volume=total_batch_size_l,
            target_ibu=recipe.data["target_ibu"],
            hops=recipe.data["boil_hops"],
        )
        print("=== Hops Additions ===")
        print_hops_table(hops_additions)
