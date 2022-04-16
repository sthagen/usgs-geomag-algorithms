"""Simulate metadata service until it is implemented.
"""


def get_instrument(observatory, start_time=None, end_time=None, metadata=None):
    """Get instrument metadata

    Args:
      observatory: observatory code
      start_time: start time to match, or None to match any.
      end_time: end time to match, or None to match any.
      metadata: use custom list, defaults to _INSTRUMENT_METADATA
    Returns:
      list of matching metadata
    """
    metadata = metadata or _INSTRUMENT_METADATA
    return [
        m
        for m in metadata
        if m["station"] == observatory
        and (end_time is None or m["start_time"] is None or m["start_time"] < end_time)
        and (start_time is None or m["end_time"] is None or m["end_time"] > start_time)
    ]


"""
To make this list easier to maintain:
 - List NT network stations first, then other networks in alphabetical order
 - Within networks, alphabetize by station, then start_time.
"""
_INSTRUMENT_METADATA = [
    {
        "network": "NT",
        "station": "BDT",
        "start_time": None,
        "end_time": None,
        "instrument": {
            "type": "FGE",
            "channels": {
                # each channel maps to a list of components to calculate nT
                # TODO: calculate these lists based on "FGE" type
                "U": [{"channel": "U_Volt", "offset": 20613, "scale": 313.2}],
                "V": [{"channel": "V_Volt", "offset": 0, "scale": 312.3}],
                "W": [{"channel": "W_Volt", "offset": 47450, "scale": 312.0}],
            },
            "electronics": {
                "serial": "E0542",
                # these scale values are used to convert voltage
                "x-scale": 313.2,  # V/nT
                "y-scale": 312.3,  # V/nT
                "z-scale": 312.0,  # V/nT
                "temperature-scale": 0.01,  # V/K
            },
            "sensor": {
                "serial": "S0419",
                # these constants combine with instrument setting for offset
                "x-constant": 36958,  # nT/mA
                "y-constant": 36849,  # nT/mA
                "z-constant": 36811,  # nT/mA
            },
        },
    },
    {
        "network": "NT",
        "station": "BOU",
        "start_time": None,
        "end_time": None,
        "instrument": {
            "type": "Narod",
            "channels": {
                "U": [
                    {"channel": "U_Volt", "offset": 0, "scale": 100},
                    {"channel": "U_Bin", "offset": 0, "scale": 500},
                ],
                "V": [
                    {"channel": "V_Volt", "offset": 0, "scale": 100},
                    {"channel": "V_Bin", "offset": 0, "scale": 500},
                ],
                "W": [
                    {"channel": "W_Volt", "offset": 0, "scale": 100},
                    {"channel": "W_Bin", "offset": 0, "scale": 500},
                ],
            },
        },
    },
    {
        "network": "NT",
        "station": "BXX",
        "start_time": None,
        "end_time": None,
        "instrument": {
            "type": "Narod",
            "channels": {
                "U": [
                    {"channel": "U_Volt", "offset": 0, "scale": 100},
                    {"channel": "U_Bin", "offset": 0, "scale": 500},
                ],
                "V": [
                    {"channel": "V_Volt", "offset": 0, "scale": 100},
                    {"channel": "V_Bin", "offset": 0, "scale": 500},
                ],
                "W": [
                    {"channel": "W_Volt", "offset": 0, "scale": 100},
                    {"channel": "W_Bin", "offset": 0, "scale": 500},
                ],
            },
        },
    },
    {
        "network": "NT",
        "station": "BRT",
        "start_time": None,
        "end_time": None,
        "instrument": {
            "type": "Narod",
            "channels": {
                "U": [
                    {"channel": "U_Volt", "offset": 0, "scale": 100},
                    {"channel": "U_Bin", "offset": 0, "scale": 506},
                ],
                "V": [
                    {"channel": "V_Volt", "offset": 0, "scale": 100},
                    {"channel": "V_Bin", "offset": 0, "scale": 505.6},
                ],
                "W": [
                    {"channel": "W_Volt", "offset": 0, "scale": 100},
                    {"channel": "W_Bin", "offset": 0, "scale": 506},
                ],
            },
        },
    },
    {
        "network": "NT",
        "station": "BRW",
        "start_time": None,
        "end_time": None,
        "instrument": {
            "type": "Narod",
            "channels": {
                "U": [
                    {"channel": "U_Volt", "offset": 0, "scale": 100},
                    {"channel": "U_Bin", "offset": 0, "scale": 506},
                ],
                "V": [
                    {"channel": "V_Volt", "offset": 0, "scale": 100},
                    {"channel": "V_Bin", "offset": 0, "scale": 505.6},
                ],
                "W": [
                    {"channel": "W_Volt", "offset": 0, "scale": 100},
                    {"channel": "W_Bin", "offset": 0, "scale": 506},
                ],
            },
        },
    },
    {
        "network": "NT",
        "station": "BSL",
        "start_time": None,
        "end_time": None,
        "instrument": {
            "type": "Narod",
            "channels": {
                "U": [
                    {"channel": "U_Volt", "offset": 0, "scale": 100},
                    {"channel": "U_Bin", "offset": 0, "scale": 500},
                ],
                "V": [
                    {"channel": "V_Volt", "offset": 0, "scale": 100},
                    {"channel": "V_Bin", "offset": 0, "scale": 500},
                ],
                "W": [
                    {"channel": "W_Volt", "offset": 0, "scale": 100},
                    {"channel": "W_Bin", "offset": 0, "scale": 500},
                ],
            },
        },
    },
    {
        "network": "NT",
        "station": "CMO",
        "start_time": None,
        "end_time": None,
        "instrument": {
            "type": "Narod",
            "channels": {
                "U": [
                    {"channel": "U_Volt", "offset": 0, "scale": 99.4},
                    {"channel": "U_Bin", "offset": 0, "scale": 502.5},
                ],
                "V": [
                    {"channel": "V_Volt", "offset": 0, "scale": 101.5},
                    {"channel": "V_Bin", "offset": 0, "scale": 512.5},
                ],
                "W": [
                    {"channel": "W_Volt", "offset": 0, "scale": 100.98},
                    {"channel": "W_Bin", "offset": 0, "scale": 509.15},
                ],
            },
        },
    },
    {
        "network": "NT",
        "station": "CMT",
        "start_time": None,
        "end_time": None,
        "instrument": {
            "type": "FGE",
            "channels": {
                # each channel maps to a list of components to calculate nT
                # TODO: calculate these lists based on "FGE" type
                "U": [{"channel": "U_Volt", "offset": 0, "scale": 967.7}],
                "V": [{"channel": "V_Volt", "offset": 0, "scale": 969.7}],
                "W": [{"channel": "W_Volt", "offset": 0, "scale": 973.4}],
            },
            "electronics": {
                "serial": "E0568",
                # these scale values are used to convert voltage
                "x-scale": 967.7,  # V/nT
                "y-scale": 969.7,  # V/nT
                "z-scale": 973.4,  # V/nT
                "temperature-scale": 0.01,  # V/K
            },
            "sensor": {
                "serial": "S0443",
                # these constants combine with instrument setting for offset
                "x-constant": 37062,  # nT/mA
                "y-constant": 37141,  # nT/mA
                "z-constant": 37281,  # nT/mA
            },
        },
    },
    {
        "network": "NT",
        "station": "DED",
        "start_time": None,
        "end_time": None,
        "instrument": {
            "type": "Narod",
            "channels": {
                "U": [
                    {"channel": "U_Volt", "offset": 0, "scale": 100},
                    {"channel": "U_Bin", "offset": 0, "scale": 508.20},
                ],
                "V": [
                    {"channel": "V_Volt", "offset": 0, "scale": 100},
                    {"channel": "V_Bin", "offset": 0, "scale": 508.40},
                ],
                "W": [
                    {"channel": "W_Volt", "offset": 0, "scale": 100},
                    {"channel": "W_Bin", "offset": 0, "scale": 508.03},
                ],
            },
        },
    },
    {
        "network": "NT",
        "station": "FDT",
        "start_time": None,
        "end_time": None,
        "instrument": {
            "type": "Narod",
            "channels": {
                "U": [
                    {"channel": "U_Volt", "offset": 0, "scale": 100},
                    {"channel": "U_Bin", "offset": 0, "scale": 500},
                ],
                "V": [
                    {"channel": "V_Volt", "offset": 0, "scale": 100},
                    {"channel": "V_Bin", "offset": 0, "scale": 500},
                ],
                "W": [
                    {"channel": "W_Volt", "offset": 0, "scale": 100},
                    {"channel": "W_Bin", "offset": 0, "scale": 500},
                ],
            },
        },
    },
    {
        "network": "NT",
        "station": "FRD",
        "start_time": None,
        "end_time": None,
        "instrument": {
            "type": "Narod",
            "channels": {
                "U": [
                    {"channel": "U_Volt", "offset": 0, "scale": 100},
                    {"channel": "U_Bin", "offset": 0, "scale": 500},
                ],
                "V": [
                    {"channel": "V_Volt", "offset": 0, "scale": 100},
                    {"channel": "V_Bin", "offset": 0, "scale": 500},
                ],
                "W": [
                    {"channel": "W_Volt", "offset": 0, "scale": 100},
                    {"channel": "W_Bin", "offset": 0, "scale": 500},
                ],
            },
        },
    },
    {
        "network": "NT",
        "station": "FRN",
        "start_time": None,
        "end_time": None,
        "instrument": {
            "type": "Narod",
            "channels": {
                "U": [
                    {"channel": "U_Volt", "offset": 0, "scale": 98.48},
                    {"channel": "U_Bin", "offset": 0, "scale": 497.50},
                ],
                "V": [
                    {"channel": "V_Volt", "offset": 0, "scale": 100.60},
                    {"channel": "V_Bin", "offset": 0, "scale": 506},
                ],
                "W": [
                    {"channel": "W_Volt", "offset": 0, "scale": 99},
                    {"channel": "W_Bin", "offset": 0, "scale": 501},
                ],
            },
        },
    },
    {
        "network": "NT",
        "station": "GUA",
        "start_time": None,
        "end_time": None,
        "instrument": {
            "type": "Narod",
            "channels": {
                "U": [
                    {"channel": "U_Volt", "offset": 0, "scale": 100},
                    {"channel": "U_Bin", "offset": 0, "scale": 500},
                ],
                "V": [
                    {"channel": "V_Volt", "offset": 0, "scale": 100},
                    {"channel": "V_Bin", "offset": 0, "scale": 500},
                ],
                "W": [
                    {"channel": "W_Volt", "offset": 0, "scale": 100},
                    {"channel": "W_Bin", "offset": 0, "scale": 500},
                ],
            },
        },
    },
    {
        "network": "NT",
        "station": "GUT",
        "start_time": None,
        "end_time": None,
        "instrument": {
            "type": "FGE",
            "channels": {
                # each channel maps to a list of components to calculate nT
                # TODO: calculate these lists based on "FGE" type
                "U": [{"channel": "U_Volt", "offset": 0, "scale": 320.0}],
                "V": [{"channel": "V_Volt", "offset": 0, "scale": 320.0}],
                "W": [{"channel": "W_Volt", "offset": 0, "scale": 320.0}],
            },
            ## this info should get updated when available
            # "electronics": {
            #     "serial": "E0542",
            #     # these scale values are used to convert voltage
            #     "x-scale": 313.2,  # V/nT
            #     "y-scale": 312.3,  # V/nT
            #     "z-scale": 312.0,  # V/nT
            #     "temperature-scale": 0.01,  # V/K
            # },
            # "sensor": {
            #     "serial": "S0419",
            #     # these constants combine with instrument setting for offset
            #     "x-constant": 36958,  # nT/mA
            #     "y-constant": 36849,  # nT/mA
            #     "z-constant": 36811,  # nT/mA
            # },
        },
    },
    {
        "network": "NT",
        "station": "HON",
        "start_time": None,
        "end_time": None,
        "instrument": {
            "type": "Narod",
            "channels": {
                "U": [
                    {"channel": "U_Volt", "offset": 0, "scale": 100},
                    {"channel": "U_Bin", "offset": 0, "scale": 500},
                ],
                "V": [
                    {"channel": "V_Volt", "offset": 0, "scale": 100},
                    {"channel": "V_Bin", "offset": 0, "scale": 500},
                ],
                "W": [
                    {"channel": "W_Volt", "offset": 0, "scale": 100},
                    {"channel": "W_Bin", "offset": 0, "scale": 500},
                ],
            },
        },
    },
    {
        "network": "NT",
        "station": "HOT",
        "start_time": None,
        "end_time": None,
        "instrument": {
            "type": "FGE",
            "channels": {
                # each channel maps to a list of components to calculate nT
                # TODO: calculate these lists based on "FGE" type
                "U": [{"channel": "U_Volt", "offset": 0, "scale": 320.0}],
                "V": [{"channel": "V_Volt", "offset": 0, "scale": 320.0}],
                "W": [{"channel": "W_Volt", "offset": 0, "scale": 320.0}],
            },
            ## this info should get updated when available
            # "electronics": {
            #     "serial": "E0542",
            #     # these scale values are used to convert voltage
            #     "x-scale": 313.2,  # V/nT
            #     "y-scale": 312.3,  # V/nT
            #     "z-scale": 312.0,  # V/nT
            #     "temperature-scale": 0.01,  # V/K
            # },
            # "sensor": {
            #     "serial": "S0419",
            #     # these constants combine with instrument setting for offset
            #     "x-constant": 36958,  # nT/mA
            #     "y-constant": 36849,  # nT/mA
            #     "z-constant": 36811,  # nT/mA
            # },
        },
    },
    {
        "network": "NT",
        "station": "NEW",
        "start_time": None,
        "end_time": None,
        "instrument": {
            "type": "Narod",
            "channels": {
                "U": [
                    {"channel": "U_Volt", "offset": 0, "scale": 100},
                    {"channel": "U_Bin", "offset": 0, "scale": 500},
                ],
                "V": [
                    {"channel": "V_Volt", "offset": 0, "scale": 100},
                    {"channel": "V_Bin", "offset": 0, "scale": 500},
                ],
                "W": [
                    {"channel": "W_Volt", "offset": 0, "scale": 100},
                    {"channel": "W_Bin", "offset": 0, "scale": 500},
                ],
            },
        },
    },
    {
        "network": "NT",
        "station": "LLO",
        "start_time": None,
        "end_time": None,
        "instrument": {
            "type": "Narod",
            "channels": {
                "U": [
                    {"channel": "U_Volt", "offset": 0, "scale": 100},
                    {"channel": "U_Bin", "offset": 0, "scale": 500},
                ],
                "V": [
                    {"channel": "V_Volt", "offset": 0, "scale": 100},
                    {"channel": "V_Bin", "offset": 0, "scale": 500},
                ],
                "W": [
                    {"channel": "W_Volt", "offset": 0, "scale": 100},
                    {"channel": "W_Bin", "offset": 0, "scale": 500},
                ],
            },
        },
    },
    {
        "network": "NT",
        "station": "SHU",
        "start_time": None,
        "end_time": None,
        "instrument": {
            "type": "Narod",
            "channels": {
                "U": [
                    {"channel": "U_Volt", "offset": 0, "scale": 100},
                    {"channel": "U_Bin", "offset": 0, "scale": 505},
                ],
                "V": [
                    {"channel": "V_Volt", "offset": 0, "scale": 100},
                    {"channel": "V_Bin", "offset": 0, "scale": 505},
                ],
                "W": [
                    {"channel": "W_Volt", "offset": 0, "scale": 100},
                    {"channel": "W_Bin", "offset": 0, "scale": 505},
                ],
            },
        },
    },
    {
        "network": "NT",
        "station": "SIT",
        "start_time": None,
        "end_time": None,
        "instrument": {
            "type": "Narod",
            "channels": {
                "U": [
                    {"channel": "U_Volt", "offset": 0, "scale": 100},
                    {"channel": "U_Bin", "offset": 0, "scale": 500},
                ],
                "V": [
                    {"channel": "V_Volt", "offset": 0, "scale": 100},
                    {"channel": "V_Bin", "offset": 0, "scale": 500},
                ],
                "W": [
                    {"channel": "W_Volt", "offset": 0, "scale": 100},
                    {"channel": "W_Bin", "offset": 0, "scale": 500},
                ],
            },
        },
    },
    {
        "network": "NT",
        "station": "SJG",
        "start_time": None,
        "end_time": None,
        "instrument": {
            "type": "Narod",
            "channels": {
                "U": [
                    {"channel": "U_Volt", "offset": 0, "scale": 100},
                    {"channel": "U_Bin", "offset": 0, "scale": 500},
                ],
                "V": [
                    {"channel": "V_Volt", "offset": 0, "scale": 100},
                    {"channel": "V_Bin", "offset": 0, "scale": 500},
                ],
                "W": [
                    {"channel": "W_Volt", "offset": 0, "scale": 100},
                    {"channel": "W_Bin", "offset": 0, "scale": 500},
                ],
            },
        },
    },
    {
        "network": "NT",
        "station": "SJT",
        "start_time": None,
        "end_time": None,
        "instrument": {
            "type": "FGE",
            "channels": {
                # each channel maps to a list of components to calculate nT
                # TODO: calculate these lists based on "FGE" type
                "U": [{"channel": "U_Volt", "offset": 0, "scale": 320.0}],
                "V": [{"channel": "V_Volt", "offset": 0, "scale": 320.0}],
                "W": [{"channel": "W_Volt", "offset": 0, "scale": 320.0}],
            },
            ## this info should get updated when available
            # "electronics": {
            #     "serial": "E0542",
            #     # these scale values are used to convert voltage
            #     "x-scale": 313.2,  # V/nT
            #     "y-scale": 312.3,  # V/nT
            #     "z-scale": 312.0,  # V/nT
            #     "temperature-scale": 0.01,  # V/K
            # },
            # "sensor": {
            #     "serial": "S0419",
            #     # these constants combine with instrument setting for offset
            #     "x-constant": 36958,  # nT/mA
            #     "y-constant": 36849,  # nT/mA
            #     "z-constant": 36811,  # nT/mA
            # },
        },
    },
    {
        "network": "NT",
        "station": "TUC",
        "start_time": None,
        "end_time": None,
        "instrument": {
            "type": "Narod",
            "channels": {
                "U": [
                    {"channel": "U_Volt", "offset": 0, "scale": 100},
                    {"channel": "U_Bin", "offset": 0, "scale": 500},
                ],
                "V": [
                    {"channel": "V_Volt", "offset": 0, "scale": 100},
                    {"channel": "V_Bin", "offset": 0, "scale": 500},
                ],
                "W": [
                    {"channel": "W_Volt", "offset": 0, "scale": 100},
                    {"channel": "W_Bin", "offset": 0, "scale": 500},
                ],
            },
        },
    },
]
