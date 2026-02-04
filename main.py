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
import system_profile as sp
from system_profile import PhysicalConstants
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
    parser = argparse.ArgumentParser(description="Brecac kalkylator", add_help=False, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
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
    parser.add_argument("--system", "-s", choices=["Braumeister20", "Braumeister20Short"], default="Braumeister20Short", help="Systemprofil att använda (Braumeister20 eller Braumeister20Short)")
    parser.add_argument("--recipe", "-r", required=True, help="Sökväg till receptfil (YAML) som ska användas")

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
    # Verifiera att receptfilen finns innan vi försöker ladda den
    if not os.path.exists(args.recipe):
        parser.error(f"Receptfil hittades inte: {args.recipe}")
    recipe = RecipeLoader(args.recipe)

    # 2. Initiera system och kalkylatorer
    system = getattr(sp, args.system)()
    logger.info("Using system profile: %s", args.system)

    boil_off_volume_l = (recipe.data.get("boil_time_min") / PhysicalConstants().minutes_per_h) * system.boil_off_l_per_hour
    total_postboil_volume_l = recipe.data["batch_size_l"] + system.trub_loss_l

    total_preboil_volume_l = total_postboil_volume_l + boil_off_volume_l
    logger.info(f"Volume preboil initially: {total_preboil_volume_l:.2f} L")
    preboil_gravity_plato = (total_postboil_volume_l/total_preboil_volume_l) * recipe.data["target_og_plato"]
    logger.info(f"Estimated pre-boil gravity: {preboil_gravity_plato:.2f} °P")


    gravity_calc = GravityCalculator(system)
    grain_bill = gravity_calc.calc_grain_bill_no_sparge(
        target_plato=preboil_gravity_plato,
        batch_size_l=total_preboil_volume_l,
        malts_percent=recipe.data["mash_fermentables"],
    )
    total_grain_kg = gravity_calc.calc_total_grain_kg(grain_bill)

    volume_mash_loss_l = gravity_calc.get_volume_loss_from_grain(total_grain_kg)
    logger.info(f"Volume loss from grain: {volume_mash_loss_l:.2f} L")
    total_preboil_volume_l = total_preboil_volume_l + volume_mash_loss_l

    logger.info(f"Volume preboil, final: {total_preboil_volume_l:.2f} L")

    # Log results
    logger = logging.getLogger(__name__)
    logger.info("=== Final mash grain bill ===")
    logger.info(f"Mash-in volume needed: {total_preboil_volume_l:.1f} L, {system.get_volume_in_mm(total_preboil_volume_l):.1f} mm from bottom")
    logger.info("Malts:")
    for item in grain_bill:
        logger.info(f"  {item['name']}: {item['amount_kg']:.1f} kg")
    logger.info(f"Total grain: {total_grain_kg:.1f} kg")

    system = getattr(sp, args.system)()

    get_num_mashes = system.get_num_mashes(total_grain_kg)
    logger.info(f"Number of mashes required: {get_num_mashes}")


    color = ColorCalculator.calculate(
        malts=grain_bill,          # grain_bill innehåller amount_kg och color_ebc
        volume_l=recipe.batch_size_l
    )

    print("MCU:", color["mcu"])
    print("EBC (Morey):", color["ebc"])


    logger.debug("Calulating fermetor fermentables:")
    grain_bill_fermentor = gravity_calc.calc_grain_bill(
        target_plato=recipe.data["target_og_plato"],
        batch_size_l=recipe.data["batch_size_l"],
        malts_percent=recipe.data["fermentor_fermentables"],
    )

    # Skriv ut fermentor-ingredienser och total vikt
    logger.info("Fermentor fermentables:")
    total_fermentor_kg = gravity_calc.calc_total_grain_kg(grain_bill_fermentor)
    for item in grain_bill_fermentor:
        logger.info(f"  {item['name']}: {item['amount_kg']:.2f} kg")
    logger.info(f"Total fermentor grain: {total_fermentor_kg:.2f} kg")



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
        bitterness_calc = BitternessCalculator()
        hops_additions = bitterness_calc.calc_hops_additions(
            plato=(preboil_gravity_plato + recipe.data["target_og_plato"]) / 2,
            volume=total_postboil_volume_l,
            target_ibu=recipe.data["target_ibu"],
            hops=recipe.data["boil_hops"],
        )
        print("=== Hops Additions ===")
        print_hops_table(hops_additions)
