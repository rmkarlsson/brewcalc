import os
import logging
import argparse
import sys

import system_profile as sp
from system_profile import PhysicalConstants


if __name__ == "__main__":
    # CLI and global logging config
    parser = argparse.ArgumentParser(description="Brewcalc converter", add_help=False, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Custom help (we disabled default -h) and hop boil calc
    parser.add_argument("-h", "--help", action="help", default=argparse.SUPPRESS, help="Visa hjälp")
    parser.add_argument("-m", "--mm_to_l", type=float, help="Convert MM to liters for the system, based on boiler diameter")
    parser.add_argument("-l", "--l_to_mm", type=float, help="Convert liters to MM for the system, based on boiler diameter")
    parser.add_argument("--system", "-s", choices=["Braumeister20", "Braumeister20Short"], default="Braumeister20Short", help="Systemprofil att använda (Braumeister20 eller Braumeister20Short)")

    args = parser.parse_args()

    # Log level is always INFO, output to stdout only.
    log_level = "INFO"

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    ))

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = []  # clear existing handlers so only stdout is used
    root_logger.addHandler(stream_handler)

    logging.getLogger(__name__).info("Starting converter (log_level=%s)", log_level)
    # module logger for later debug output
    logger = logging.getLogger(__name__)

    # 2. Initiera system och kalkylatorer
    system = sp.get_system_profile(args.system)
    logger.info("Using system profile: %s", args.system)

    if args.l_to_mm is not None:
        volume_l = system.get_volume_in_mm(args.l_to_mm)
        logger.info("%f liters is %d mm in the tun", args.l_to_mm, volume_l)
    if args.mm_to_l is not None:
        liters = system.get_volume_l(args.mm_to_l)
        logger.info("%d mm is %.1f L in the tun", args.mm_to_l, liters)
