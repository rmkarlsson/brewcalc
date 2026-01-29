MALTS_DB = {
    "Pale Ale Malt": {
        "extract_percent": 0.80,
        "color_ebc": 6
    },
    "Pilsner Malt": {
        "extract_percent": 0.81,
        "color_ebc": 3
    },
    "Carapils": {
        "extract_percent": 0.72,
        "color_ebc": 4
    },
    "Munich Malt": {
        "extract_percent": 0.78,
        "color_ebc": 15
    }
}


def get_malt(name: str):
    try:
        return MALTS_DB[name]
    except KeyError:
        raise ValueError(f"Maltsort saknas i databasen: {name}")