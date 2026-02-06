from dataclasses import dataclass


@dataclass
class Gravities:
    """
    Representerar volymerna före och efter kok.
    """
    pre_boil: float  # Volym innan kok (L)
    post_boil: float  # Volym efter kok (L)

    def __init__(self, post_boil: float):
        self.post_boil = post_boil

