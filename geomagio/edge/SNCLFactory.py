from typing import Optional

from .SNCL import SNCL, INTERVAL_CONVERSIONS, ELEMENT_CONVERSIONS


class SNCLFactory(object):
    def __init__(self, data_format: str = "miniseed"):
        self.data_format = data_format

    def get_sncl(
        self,
        station: str,
        data_type: str,
        element: str,
        interval: str,
        network: str = "NT",
    ) -> SNCL:
        return SNCL(
            station=station,
            network=network,
            channel=self.get_channel(element=element, interval=interval),
            location=self.get_location(element=element, data_type=data_type),
        )

    def get_channel(self, element: str, interval: str) -> str:
        channel_start = self.__get_channel_start(interval=interval)
        channel_end = self.__get_predefined_channel(element=element)
        channel_end = channel_end or self.__get_channel_end(element=element)
        return channel_start + channel_end

    def get_location(self, element: str, data_type: str) -> str:
        location_start = self.__get_location_start(data_type=data_type)
        location_end = self.__get_location_end(element=element)
        return location_start + location_end

    def __get_channel_start(self, interval: str) -> str:
        try:
            return INTERVAL_CONVERSIONS[self.data_format][interval]
        except:
            raise ValueError(f"Unexpected interval: {interval}")

    def __get_predefined_channel(self, element: str) -> Optional[str]:
        if len(element) == 3 and "-" not in element and element != "DST":
            return element[1:]
        elif element in ELEMENT_CONVERSIONS:
            return ELEMENT_CONVERSIONS[element]
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
        if "_Sat" in element:
            return "1"
        if "_Dist" in element:
            return "D"
        if "_SQ" in element:
            return "Q"
        if "_SV" in element:
            return "V"
        return "0"
