import os
import logging
import argparse
import sys

from gravities import Gravities
from volumes import Volumes

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


from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def print_recipe(recipe, malt_bill, fermentor_fermentables, hop_additions, gravities, volumes, system):
    # Titelpanel
    console.print(Panel(
        f'{recipe["name"]}, {recipe["target_og_plato"]} L, {recipe["target_og_plato"]} °P, rev: {recipe["version"]}',
        style="bold cyan",
        expand=False
    ))


    # Malt-tabell
    vol= Table(title="Volumes", show_lines=True)
    vol.add_column("Phase", style="bold")
    vol.add_column("Volume", justify="right")
    vol.add_column("Plato", justify="right")
    vol.add_row("Mash-in", f"{(volumes.pre_boil + volumes.mash_loss):.2f} L, {system.get_volume_in_mm(volumes.pre_boil + volumes.mash_loss):.2f} mm", f"0 °P")
    vol.add_row("Pre-boil", f"{volumes.pre_boil:.2f} L, {system.get_volume_in_mm(volumes.pre_boil):.2f} mm", f"{gravities.pre_boil:.2f} °P")
    vol.add_row("Post-boil", f"{volumes.post_boil:.2f} L (trub {volumes.trub_loss:.2f} L), {system.get_volume_in_mm(volumes.post_boil):.2f} mm", f"{gravities.post_boil:.2f} °P")

    console.print(vol)

    # Malt-tabell
    malt = Table(title="Mash fermentables", show_lines=True)
    malt.add_column("Namn", style="bold")
    malt.add_column("Amount [kg]", justify="right")

    for f in malt_bill:
        malt.add_row(
            f["name"],
            f"{f['amount_kg']:.2f} kg"
        )

    console.print(malt)

    # Humle-tabell
    hops = Table(title="Hops", show_lines=True)
    hops.add_column("Name")
    hops.add_column("Amount [g]", justify="right")
    hops.add_column("Time [min]", justify="right")

    for h in hop_additions:
        hops.add_row(
            h["name"],
            f'{h["weight"]:.1f}',
            f"{h['boil_time_min']} min"
        )

    console.print(hops)

    f_m = Table(title="Fermentor fermentables", show_lines=True)
    f_m.add_column("Namn", style="bold")
    f_m.add_column("Amount [kg]", justify="right")

    for f in fermentor_fermentables:
        f_m.add_row(
            f["name"],
            f"{f['amount_kg']:.2f} kg"
        )
    console.print(f_m)





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

    volumes = Volumes(trub_loss=system.trub_loss_l, post_boil=recipe.data["batch_size_l"])
    logger.info(f"Volume preboil initially: {volumes.post_boil:.2f} L")
    
    gravity_calc = GravityCalculator(system)
    gravities = Gravities(gravity_calc.get_pre_boil_plato(recipe.data["mash_fermentables"], recipe.data["target_og_plato"]))

    volumes.boil_off = (recipe.data.get("boil_time_min") / PhysicalConstants().minutes_per_h) * system.boil_off_l_per_hour
    volumes.post_boil = recipe.data["batch_size_l"] + system.trub_loss_l
    logger.info(f"Volume post-boil: {volumes.post_boil:.2f} L, including trub loss {system.trub_loss_l:.2f} L")

    volumes.pre_boil = volumes.post_boil + volumes.boil_off
    logger.info(f"Volume preboil before mash compenation: {volumes.pre_boil:.2f} L, including boil off {volumes.boil_off:.2f} L")
    gravities.pre_boil = (volumes.post_boil/volumes.pre_boil) * gravities.post_boil
    logger.info(f"Estimated pre-boil gravity: {gravities.pre_boil:.2f} °P based on post-boil gravity {gravities.post_boil:.2f} °P and volumes reduction {(volumes.post_boil/volumes.pre_boil):.2f}")
    volumes.mash_loss = 0
    
    max_iter = 5
    gravity_calc = GravityCalculator(system)
    grain_bill = []
    grain_bill_change = 1000.0
    total_grain_kg = 0.0
    while grain_bill_change > 0.1 :
        grain_bill = gravity_calc.calc_grain_bill(
            target_plato=gravities.pre_boil,
            batch_size_l=volumes.get_total_pre_boil(),
            malts_percent=recipe.data["mash_fermentables"],
        )
        new_total_grain_kg = gravity_calc.calc_total_grain_kg(grain_bill)
        grain_bill_change = abs(total_grain_kg - new_total_grain_kg)
        total_grain_kg = new_total_grain_kg
        volumes.mash_loss = gravity_calc.get_volume_loss_from_grain(total_grain_kg)
        logger.info(f"Volume loss from grain: {volumes.mash_loss:.2f} L, total grain bill: {total_grain_kg:.2f} kg")



    logger.info(f"Volume preboil, final: { volumes.get_total_pre_boil():.2f} L")
    # Log results
    logger = logging.getLogger(__name__)
    logger.info("=== Final mash grain bill ===")
    logger.info(f"Mash-in volume needed: { volumes.get_total_pre_boil():.1f} L, {system.get_volume_in_mm( volumes.get_total_pre_boil()):.1f} mm from bottom")
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


    hops_additions = []
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
    else:
        bitterness_calc = BitternessCalculator()
        hops_additions = bitterness_calc.calc_hops_additions(
            plato=(gravities.pre_boil + gravities.post_boil) / 2,
            volume=volumes.pre_boil,
            target_ibu=recipe.data["target_ibu"],
            hops=recipe.data["boil_hops"],
        )

    print_recipe(recipe.summary(), grain_bill, grain_bill_fermentor, hops_additions, gravities, volumes, system)
