from typing import Dict, Optional, Set

from pydantic import BaseModel

INTERVAL_CONVERSIONS = {
    "legacy": {
        "second": "S",
        "minute": "M",
        "hour": "H",
        "day": "D",
    },
    "miniseed": {
        "tenhertz": "B",
        "second": "L",
        "minute": "U",
        "hour": "R",
        "day": "P",
    },
}
ELEMENT_CONVERSIONS = {
    # e-field
    "E-E": "QE",
    "E-N": "QN",
    # derived indicies
    "Dst3": "X3",
    "Dst4": "X4",
    "SQ": "SQ",
    "SV": "SV",
    "DIST": "DT",
    "DST": "GD",
}

CHANNEL_CONVERSIONS = {
    ELEMENT_CONVERSIONS[key]: key for key in ELEMENT_CONVERSIONS.keys()
}


class SNCL(BaseModel):
    station: str
    network: str = "NT"
    channel: str
    location: str
    data_format: str = "miniseed"

    def dict(self, exclude: Set = {"data_format"}) -> dict:
        return super().dict(
            exclude=exclude,
        )

    def json(self, exclude: Set = {"data_format"}) -> str:
        return super().json(
            exclude=exclude,
        )

    @property
    def data_type(self) -> str:
        location_start = self.location[0]
        if location_start == "R":
            return "variation"
        elif location_start == "A":
            return "adjusted"
        elif location_start == "Q":
            return "quasi-definitive"
        elif location_start == "D":
            return "definitive"
        raise ValueError(f"Unexpected location start: {location_start}")

    @property
    def element(self) -> str:
        element = self.__get_predefined_element()
        element = element or self.__get_element()
        return element

    @property
    def interval(self) -> str:
        interval_conversions = INTERVAL_CONVERSIONS[self.data_format]
        interval_code_conversions = {
            interval_conversions[key]: key for key in interval_conversions.keys()
        }
        channel_start = self.channel[0]
        try:
            return interval_code_conversions[channel_start]
        except:
            raise ValueError(f"Unexcepted interval code: {channel_start}")

    def __get_element(self):
        element_start = self.channel[2]
        channel = self.channel
        channel_middle = channel[1]
        location_end = self.location[1]
        if channel_middle in ["Q", "E"]:
            element_end = "_Volt"
        elif channel_middle == "Y":
            element_end = "_Bin"
        elif channel_middle == "K":
            element_end = "_Temp"
        elif location_end == "1":
            element_end = "_Sat"
        elif location_end == "D":
            element_end = "_Dist"
        elif location_end == "Q":
            element_end = "_SQ"
        elif location_end == "V":
            element_end = "_SV"
        else:
            element_end = ""
        return element_start + element_end

    def __get_predefined_element(self) -> Optional[str]:
        channel = self.channel
        channel_end = channel[1:]
        if channel_end in CHANNEL_CONVERSIONS:
            return CHANNEL_CONVERSIONS[channel_end]
        return None
