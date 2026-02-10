from dataclasses import dataclass


@dataclass
class Volumes:
    """
    Representerar volymerna före och efter kok.
    """
    mash_in: float  # Volym innan kok (L)
    pre_boil: float  # Volym innan kok (L)
    post_boil: float  # Volym efter kok (L)
    mash_loss: float  # Volymförlust i mäskning (L)
    boil_off: float  # Volymförlust under kok (L)
    trub_loss: float  # Volymförlust i trub (L)

    def __init__(self, trub_loss: float, post_boil: float):
        self.trub_loss = trub_loss
        self.post_boil = post_boil
        self.pre_boil = 0.0
        self.mash_loss = 0.0
        self.boil_off = 0.0

    def get_total_pre_boil(self) -> float:
        """
        Total volym som behövs innan kok, inklusive mäskförluster.
        """
        return self.pre_boil + self.mash_loss