HOPS_DB = {
    "Cascade": {
        "alpha_acid": 0.055,
    },
    "Centennial": {
        "alpha_acid": 0.10,
    },
    "Saaz": {
        "alpha_acid": 0.035,
    },
    "Magnum": {
        "alpha_acid": 0.10,
    }
}

def get_hop(name):
    try:
        return HOPS_DB[name]
    except KeyError:
        raise ValueError(f"Humlesort saknas i databasen: {name}")