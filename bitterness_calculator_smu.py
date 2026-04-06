import math
from typing import Dict, List
import logging
import copy

from pygments.lexer import this
from hop import Hop
from hops_db import get_hop
from system_profile import PhysicalConstants
from gravity_calculator import GravityCalculator

# Module logger
logger = logging.getLogger(__name__)



class BitternessCalculatorSMU:
    WORT_CLARITY_VALUES: Dict[str, float] = {
        "very clear": 1.30,
        "clear": 1.20,
        "somewhat clear": 1.10,
        "average (default)": 1.00,
        "somewhat cloudy": 0.90,
        "cloudy": 0.80,
        "very cloudy": 0.70,
        "extremely cloudy": 0.60,
    }


    KRAUSEN_VALUE: Dict[str, float] = {
        "mix krausen back in; no loss": 1.1268, # see beer64/analyze.tcl = 1.0/0.8875
        "minor krausen deposits on FV": 1.0500, # 'medium' * 1.05
        "medium krausen deposits on FV (default)": 1.0000, # see beer64/analyze.tcl, normalize 0.8875 to 1.0
        "heavy krausen deposits on FV": 0.9500, # 'medium' * 0.95
        "very heavy krausen deposits on FV": 0.9000, # 'medium' * 0.90
        "blow off krausen with slow fermentation": 0.9380,  # 'medium' * 0.938;
        "blow off krausen with normal fermentation": 0.8330,  # 'medium' * 0.833;
        "blow off krausen with vigorous fermentation": 0.7290,  # 'medium' * 0.729;
    }

    fermentationFactor: float = 0.85
    IAA_LF_boil: float = 0.51

    def __init__(self):
        pass

    @classmethod
    def get_wort_clarity_value(cls, description: str) -> float:
        if description is None:
            raise ValueError("Wort clarity description is required")

        desc = description.strip().lower()
        if desc in cls.WORT_CLARITY_VALUES:
            return cls.WORT_CLARITY_VALUES[desc]

        try:
            return float(desc)
        except ValueError as exc:
            raise ValueError(f"Unknown wort clarity description: {description}") from exc

    #------------------------------------------------------------------------------
    # Estimate post-boil pH from pre-boil pH
    @staticmethod
    def compute_postBoil_pH(preBoilpH:float, boiltime_min: int) -> float:
        pH = preBoilpH
        # see pH_function_of_temp/fitTimeData_ORIG.tcl
        # var slopeSlope = -0.002800223086542374;
        # var slopeIntercept = 0.013184013161963867;

        # this function based on data but doesn't generalize as well
        # pH = (preBoilpH * ((slopeSlope * ibu.boilTime.value) + 1.0)) +
        # (slopeIntercept * ibu.boilTime.value);
        pH = preBoilpH - (boiltime_min * 0.10 / 60.0);
  
        logging.debug(f"pre-boil pH: {preBoilpH:.4f} becomes {pH:.4f} after {boiltime_min}-minute boil");
  
        return pH

    #------------------------------------------------------------------------------
    # Compute loss factor for IAA based on pH, preboil pH is povided
    @staticmethod
    def compute_LF_IAA_pH(pH: float, boiltime_min: int) -> float:
        LF_pH = 1.0
        preBoilpH = pH

        # If pre-boil pH, estimate the post-boil pH which is the
        # one we want to base losses on.
        pH = BitternessCalculatorSMU.compute_postBoil_pH(preBoilpH, boiltime_min)

        # formula from blog post 'The Effect of pH on Utilization and IBUs'
        LF_pH = (0.071 * pH) + 0.592
    
        # if pH is low enough for a negative loss factor, set it to zero
        if LF_pH < 0.0:
            LF_pH = 0.0
        logging.debug(f"pH = {pH}, LF for IAA = {LF_pH:.4f}")

        return LF_pH

    # -----------------------------------------------------------------------------
    # compute loss factor for IAA components caused by wort turbidity
    def compute_LF_IAA_wortClarity(self, description: str) -> float:
        LF_wortClarity = self.get_wort_clarity_value(description)
        logger.debug("LF wort clarity : %.4f", LF_wortClarity)
        return LF_wortClarity
    


    # ------------------------------------------------------------------------------
    # Compute IAA loss factor (LF) during fermentation given amount of flocculation
    # Assume that fermentation affects IAA and nonIAA equally.
    @staticmethod
    def compute_LF_ferment(flocculation: str) -> float:
        LF_ferment = 0.0
        LF_flocculation = 0.0

        # The factors here come from Garetz, p. 140
        if (flocculation == "high") :
            LF_flocculation = 0.95
        elif (flocculation == "medium") :
            LF_flocculation = 1.00
        elif (flocculation == "low") :
            LF_flocculation = 1.05
        else :
            logging.error("ERROR: unknown flocculation value: %s", flocculation)
            LF_flocculation = 1.00


        LF_ferment = SMPH.fermentationFactor * LF_flocculation
        logging.debug("LF ferment : %s", LF_ferment.toFixed(4));
  
        return LF_ferment

    # -----------------------------------------------------------------------------
    # compute loss factor for IAA components caused by krausen loss
    @staticmethod
    def compute_LF_IAA_krausen(krausen_description: str) -> float:
        LF_krausen = 1.0

        desc = krausen_description.strip().lower()
        if desc in BitternessCalculatorSMU.KRAUSEN_VALUES:
            return BitternessCalculatorSMU.KRAUSEN_VALUES[desc]

        try:
            logging.debug("LF IAA krausen : %s", f"{LF_krausen:.4f}")
            return float(desc)
        except ValueError as exc:
            raise ValueError(f"Unknown krausen description: {krausen_description}") from exc


    # ------------------------------------------------------------------------------
    # Compute loss factor (LF) for finings.
    # Assume that finings affect IAA and nonIAA equally
    @staticmethod
    def compute_LF_finings(volume_l: float, amount_ml: int, finings_type: str) -> float:

        if (volume_l <= 0):
            return 0.0

        LF_finings = 1.0
        if (amount_ml > 0):
            finingsMlPerLiter = amount_ml / volume_l
            if (finings_type == "gelatin"):
                # exponential decay factor from 'gelatin' subdirectory, data.txt
                LF_finings = math.exp(-0.09713 * finingsMlPerLiter)
        logging.debug(f"LF finings : {LF_finings:.4f} from {amount_ml} ml of {finings_type} in {volume_l:.2f} l fermentor")
        return LF_finings


  
    # Compute IAA loss factor (LF) based on original gravity
    # Assume that OG affects IAA and nonIAA equally
    @staticmethod
    def compute_LF_OG_SMPH(hop: Hop, original_gravity: float, boil_time_min: int) -> float:
        LF_OG = 0.0
        # I use plato, Americans use OG, so convert to OG for the formula
        OG = GravityCalculator.plato_to_og(original_gravity)
        slope = 0.0
        t = hop.effective_steep_time

        # at 30 minutes and below, OG has no effect on IBUs.
        # at 40 minutes and above, OG affects IBUs according to the exponential
        #    equation with slope = 4.91.  This formula was fit to the data
        #    at time = 40 in the second experiment of blog post
        #    'Specific Gravity and IBUs'.
        # between 30 and 40 minutes, do a linear interpolation of 'slope'
        #     from having no effect to having full effect.

        if (OG <= 1.0) :
            return 1.0
        if (t <= 30):
            return 1.0
        
        slope = 4.91
        if (t < 40):
             slope = 0.391 * (t - 30.0) + 1.0
        LF_OG = 1.0 - 2.0*Math.exp(-1.0/(slope*(OG-1.0)))
        logging.debug(f"LF OG : {LF_OG:.4f}")
        return LF_OG



    #------------------------------------------------------------------------------
    # Compute overall loss factor (LF) for IAA, given loss factors caused by
    # the boil, pH, gravity, clarity, fermentation/flocculation, krausen,
    # finings, filtering, and age of beer.
    def compute_LF_IAA(preboil_ph: float, boil_time_min: int, hop: Hop, original_gravity: float, wort_clarity_description: str) -> float:

        LF_IAA = BitternessCalculatorSMU.IAA_LF_boil * compute_LF_IAA_pH(preboil_ph, boil_time_min) *
        compute_LF_OG_SMPH((hop, original_gravity, boil_time_min) *
        compute_LF_IAA_wortClarity(wort_clarity_description) *
        compute_LF_ferment(ibu) * compute_LF_IAA_krausen(ibu) *
        compute_LF_finings(ibu) * compute_LF_filtering(ibu) *
        compute_LF_age(ibu);
  if (SMPH.verbose > 3) {
    console.log("    IAA LF = " + LF_IAA.toFixed(4) +
              ", from LF_boil=" + SMPH.IAA_LF_boil.toFixed(4) +
              ", LF_pH=" + compute_LF_IAA_pH(ibu).toFixed(4) +
              ", LF_OG=" + compute_LF_OG_SMPH(ibu, hopIdx).toFixed(4) +
              ", LF_clarity=" + compute_LF_IAA_wortClarity(ibu).toFixed(4) +
              ", LF_ferment=" + compute_LF_ferment(ibu).toFixed(4));
    console.log("                          " +
              "LF_kausen="+ compute_LF_IAA_krausen(ibu).toFixed(4) +
              ", LF_finings=" + compute_LF_finings(ibu).toFixed(4) +
              ", LF_filtering=" + compute_LF_filtering(ibu).toFixed(4) +
              ", LF_age=" + compute_LF_age(ibu).toFixed(4));
  }
  return LF_IAA;
}



    def compute_IAA_LF_dryHop(self, volume: float, dry_hops: List[Hop], boil_hops: List[Hop]) -> float:

        dryHops_concent = 0.0
        IAA_beer = 0.0
        for hop in boil_hops:
            IAA_beer += hop.IAA_wort * compute_LF_IAA(ibu, hopIdx)
        for hop in dry_hops:
            dryHops_concent += hop.amount_g * 1000.0 / volume
  
        logging.debug(f"IAA in beer before dry hop: {} ppm", IAA_beer")
        logging.debug(f"total [dry hops]: {} ppm", dryHops_concent)
  

        # if no dry hopping, then no IAA loss
        if dryHops_concent == 0.0:
            return 1.0

        slope  =  0.0000035294117647058825
        offset = -0.000056470588235294126
        b = slope * IAA_beer + offset
        if b < 0.0:
            b = 0.0

        IAA_LF_dryHop = 0.50 * Math.exp(-1.0 * b * dryHops_concent) + 0.50

        return IAA_LF_dryHop