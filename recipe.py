from pydantic import BaseModel, ConfigDict, field_validator
import yaml
from pathlib import Path


class Fermentable(BaseModel):
    name: str
    percent: float


class Fining(BaseModel):
    name: str
    amount_ml: float


class BoilHop(BaseModel):
    name: str
    percent: float
    boil_time_min: float


class DryHop(BaseModel):
    name: str
    amount_g_per_l: float
    contact_time_days: float


class Ion(BaseModel):
    name: str
    salt_name: str
    amount_mg_per_l: float


class Recipe(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    name: str
    version: str | float
    batch_size_l: float
    boil_time_min: float
    target_og_plato: float
    target_ibu: float
    mash_fermentables: list[Fermentable]
    ambient_temperature_c: float = 20.0
    mash_ph: float | None = None
    fining: list[Fining] | None = None
    fermentor_fermentables: list[Fermentable] | None = None
    boil_hops: list[BoilHop] | None = None
    dry_hops: list[DryHop] | None = None
    ions: list[Ion] | None = None
    comments: list[str] | None = None


def load_recipe(yaml_path: str) -> Recipe:
    """
    Läser en recept-YAML-fil och skapar ett Recipe-objekt med validering.
    
    Args:
        yaml_path: Sökväg till YAML-fil (relativ eller absolut)
        
    Returns:
        Recipe: Validerat Recipe-objekt
        
    Raises:
        FileNotFoundError: Om filen inte finns
        ValueError: Om validering misslyckas
    """
    path = Path(yaml_path)
    
    # Om sökvägen är relativ, antag recipes/-mappen
    if not path.is_absolute() and not str(path).startswith("recipes/"):
        path = Path("recipes") / path
    
    if not path.exists():
        raise FileNotFoundError(f"Receptfil hittades inte: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    # Skapa och validera Recipe-objekt
    recipe = Recipe(**data)
    
    return recipe
