from pydantic import BaseModel


class Fermentable(BaseModel):
    name: str
    percent: float


class Fining(BaseModel):
    name: str
    amount_ml: float

class Hop(BaseModel):
    name: str
    percent: float
    boil_time_min: float


class Recipe(BaseModel):
    name: str
    batch_size_l: float
    fermentables: list[dict]
    fining: list[dict] | None = None
    fermentor_fermentables: list[dict] | None = None
    boil_hops: list[dict] | None = None


name: Black IPA
version: 1.1
batch_size_l: 10.0
boil_time_min: 120
target_og_plato: 12
target_ibu: 5.0
mash_ph: 5.2

mash_fermentables:
  - name: Best a-xl
    percent: 40
  - name: Unmalted wheat
    percent: 60

fining:
  - name: Irish moss
    amount_g: 5

fermentor_fermentables:

boil_hops:
  - name: Magnum
    percent: 100
    boil_time_min: 60

dry_hops:
