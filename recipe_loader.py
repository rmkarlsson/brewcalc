import yaml
import logging
from typing import Dict, Any, List

# Module logger
logger = logging.getLogger(__name__)


class RecipeLoader:
    """
    Läser in receptet och validerar:
    - mash_fermentables + fermentor_fermentables = 100 %
    - boil_hops = 100 %
    - dry_hops i g/L (ingen procent)
    """

    def __init__(self, path: str):
        self.path = path
        self.data = self._load_yaml()

        logger.debug("Loaded recipe data from %s", self.path)

        self._validate_mash_and_fermentor_percent()
        self._validate_boil_hops_percent()

    # ---------------------------------------------------------
    # YAML loader
    # ---------------------------------------------------------

    def _load_yaml(self) -> Dict[str, Any]:
        logger.debug("Loading YAML from %s", self.path)
        with open(self.path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        logger.debug("YAML loaded: keys=%s", list(data.keys()) if isinstance(data, dict) else type(data))
        return data

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def _validate_mash_and_fermentor_percent(self):
        mash = self.data.get("mash_fermentables", [])
        ferm = self.data.get("fermentor_fermentables", [])

        mash_sum = sum(m.get("percent", 0) for m in mash)
        ferm_sum = sum(f.get("percent", 0) for f in ferm)

        total = mash_sum + ferm_sum
        logger.debug("mash_fermentables sum: %.2f, fermentor_fermentables sum: %.2f", mash_sum, ferm_sum)
        

        if abs(total - 100) > 0.01:
            msg = (
                f"mash_fermentables + fermentor_fermentables måste summera till 100 %, "
                f"men är {total:.2f} %."
            )
            logger.error(msg)
            raise ValueError(msg)

    def _validate_boil_hops_percent(self):
        hops = self.data.get("boil_hops", [])
        total = sum(h.get("percent", 0) for h in hops)

        if abs(total - 100) > 0.01:
            msg = f"boil_hops måste summera till 100 %, men är {total:.2f} %."
            logger.error(msg)
            raise ValueError(msg)

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def name(self) -> str:
        return self.data.get("name", "Okänt recept")

    @property
    def version(self) -> str:
        return self.data.get("version", "Okänt recept")

    @property
    def batch_size_l(self) -> float:
        return float(self.data["batch_size_l"])

    @property
    def boil_time_min(self) -> float:
        return float(self.data["boil_time_min"])

    @property
    def target_og_plato(self) -> float:
        return float(self.data["target_og_plato"])

    @property
    def target_ibu(self) -> float:
        return float(self.data.get("target_ibu", 0))

    @property
    def mash_fermentables(self) -> List[Dict[str, Any]]:
        return self.data.get("mash_fermentables", [])

    @property
    def fermentor_fermentables(self) -> List[Dict[str, Any]]:
        return self.data.get("fermentor_fermentables", [])

    @property
    def boil_hops(self) -> List[Dict[str, Any]]:
        return self.data.get("boil_hops", [])

    @property
    def dry_hops(self) -> List[Dict[str, Any]]:
        return self.data.get("dry_hops", [])

    # ---------------------------------------------------------
    # Summary helper
    # ---------------------------------------------------------

    def summary(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "batch_size_l": self.batch_size_l,
            "boil_time_min": self.boil_time_min,
            "target_og_plato": self.target_og_plato,
            "target_ibu": self.target_ibu,
            "mash_fermentables": self.mash_fermentables,
            "fermentor_fermentables": self.fermentor_fermentables,
            "boil_hops": self.boil_hops,
            "dry_hops": self.dry_hops,
        }