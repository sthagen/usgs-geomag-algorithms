from __future__ import annotations
from typing import Optional

from .SNCL import SNCL

ELEMENT_CONVERSIONS = {
    # e-field
    "E-E": "QE",
    "E-N": "QN",
    # derived indicies
    "SQ": "SQ",
    "SV": "SV",
    "DIST": "DT",
    "DST": "GD",
}
CHANNEL_CONVERSIONS = {
    ELEMENT_CONVERSIONS[key]: key for key in ELEMENT_CONVERSIONS.keys()
}


class LegacySNCL(SNCL):
    def get_sncl(
        self,
        station: str,
        data_type: str,
        interval: str,
        element: str,
    ) -> LegacySNCL:
        from .SNCLFactory import SNCLFactory

        factory = SNCLFactory(data_format="legacy")
        return LegacySNCL(
            station=station,
            network=self.network,
            channel=factory.get_channel(element=element, interval=interval),
            location=factory.get_location(element=element, data_type=data_type),
        )

    @property
    def element(self) -> str:
        predefined_element = self.__check_predefined_element()
        element = self.__get_element()
        return predefined_element or element

    @property
    def interval(self) -> str:
        channel_start = self.channel[0]
        if channel_start == "S":
            return "second"
        elif channel_start == "M":
            return "minute"
        elif channel_start == "H":
            return "hour"
        elif channel_start == "D":
            return "day"
        raise ValueError(f"Unexcepted interval code: {channel_start}")

    def __get_element(self):
        """Translates channel/location to element"""
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
        else:
            element_end = ""
        return element_start + element_end

    def __check_predefined_element(self) -> Optional[str]:
        channel = self.channel
        channel_end = channel[1:]
        if channel_end in CHANNEL_CONVERSIONS:
            return CHANNEL_CONVERSIONS[channel_end]
        return None
