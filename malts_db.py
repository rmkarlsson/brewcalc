MALTS_DB = {
    "Pale Ale Malt": {
        "extract_percent": 0.80,
        "color_ebc": 6
    },
    "Best a-xl": {
        "extract_percent": 0.80,
        "color_ebc": 3
    },
    "Caramunich 3": {
        "extract_percent": 0.73,
        "color_ebc": 150
    },
    "Carapils": {
        "extract_percent": 0.72,
        "color_ebc": 4
    },
    "Munich I": {
        "extract_percent": 0.78,
        "color_ebc": 15
    },
    "Munich II": {
        "extract_percent": 0.78,
        "color_ebc": 22
    },
    "Carafa special 2": {
        "extract_percent": 0.72,
        "color_ebc": 1150
    },
    "Unmalted wheat": {
        "extract_percent": 0.73,
        "color_ebc": 3
    },    
    "Socker": {
        "extract_percent": 1.0,
        "color_ebc": 0
    }
}


def get_malt(name: str):
    try:
        return MALTS_DB[name]
    except KeyError:
        raise ValueError(f"Maltsort saknas i databasen: {name}")