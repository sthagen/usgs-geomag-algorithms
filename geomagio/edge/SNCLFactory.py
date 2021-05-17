from typing import Literal, Optional, Union

from .SNCL import SNCL, ELEMENT_CONVERSIONS as MINISEED_CONVERSIONS
from .LegacySNCL import LegacySNCL, ELEMENT_CONVERSIONS as LEGACY_CONVERSIONS

INTERVAL_CONVERSIONS = {
    "miniseed": {
        "tenhertz": "B",
        "second": "L",
        "minute": "U",
        "hour": "R",
        "day": "P",
    },
    "legacy": {
        "second": "S",
        "minute": "M",
        "hour": "H",
        "day": "D",
    },
}


class SNCLFactory(object):
    def __init__(self, data_format: Literal["miniseed", "legacy"] = "miniseed"):
        self.data_format = data_format

    def get_sncl(
        self,
        station: str,
        network: str,
        channel: str,
        location: str,
    ) -> Union[SNCL, LegacySNCL]:
        sncl_params = {
            "station": station,
            "network": network,
            "channel": channel,
            "location": location,
        }
        return (
            SNCL(**sncl_params)
            if self.data_format == "miniseed"
            else LegacySNCL(**sncl_params)
        )

    def get_channel(self, element: str, interval: str) -> str:
        predefined_channel = self.__check_predefined_channel(
            element=element, interval=interval
        )
        channel_start = self.__get_channel_start(interval=interval)
        channel_end = self.__get_channel_end(element=element)
        return predefined_channel or (channel_start + channel_end)

    def get_location(self, element: str, data_type: str) -> str:
        location_start = self.__get_location_start(data_type=data_type)
        location_end = self.__get_location_end(element=element)
        return location_start + location_end

    def __get_channel_start(self, interval: str) -> str:
        interval_conversions = INTERVAL_CONVERSIONS[self.data_format]
        try:
            return interval_conversions[interval]
        except:
            raise ValueError(f"Unexpected interval: {interval}")

    def __check_predefined_channel(self, element: str, interval: str) -> Optional[str]:
        channel_conversions = (
            MINISEED_CONVERSIONS
            if self.data_format == "miniseed"
            else LEGACY_CONVERSIONS
        )

        if element in channel_conversions:
            return (
                self.__get_channel_start(interval=interval)
                + channel_conversions[element]
            )
        elif len(element) == 3:
            return element
        # chan.loc format
        elif "." in element:
            channel = element.split(".")[0]
            return channel.strip()
        else:
            return None

    def __get_channel_end(self, element: str) -> str:
        channel_middle = "F" if self.data_format == "miniseed" else "V"
        if "_Volt" in element:
            channel_middle = "E"
        elif "_Bin" in element:
            channel_middle = "Y"
        elif "_Temp" in element:
            channel_middle = "K"
        elif element in ["F", "G"] and self.data_format == "legacy":
            channel_middle = "S"
        channel_end = element.split("_")[0]
        return channel_middle + channel_end

    def __get_location_start(self, data_type: str) -> str:
        """Translates data type to beginning of location code"""
        if data_type == "variation":
            return "R"
        elif data_type == "adjusted":
            return "A"
        elif data_type == "quasi-definitive":
            return "Q"
        elif data_type == "definitive":
            return "D"
        raise ValueError(f"Unexpected data type: {data_type}")

    def __get_location_end(self, element: str) -> str:
        """Translates element suffix to end of location code"""
        if "_Sat" in element:
            return "1"
        if self.data_format == "miniseed":
            if "_Dist" in element:
                return "D"
            if "_SQ" in element:
                return "Q"
            if "_SV" in element:
                return "V"
        return "0"
