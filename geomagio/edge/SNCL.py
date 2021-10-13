from typing import Dict, Optional

from pydantic import BaseModel

ELEMENT_CONVERSIONS = {
    # e-field
    "E-E": "QE",
    "E-N": "QN",
    # derived indicies
    "Dst3": "X3",
    "Dst4": "X4",
    # temperatures
    "T1": "K1",
    "T2": "K2",
    "T3": "K3",
    "T4": "K4",
}

CHANNEL_CONVERSIONS = {
    ELEMENT_CONVERSIONS[key]: key for key in ELEMENT_CONVERSIONS.keys()
}


class SNCL(BaseModel):
    station: str
    network: str = "NT"
    channel: str
    location: str

    @classmethod
    def get_sncl(
        cls,
        data_type: str,
        element: str,
        interval: str,
        station: str,
        network: str = "NT",
        location: Optional[str] = None,
    ) -> "SNCL":
        return SNCL(
            station=station,
            network=network,
            channel=get_channel(
                element=element, interval=interval, data_type=data_type
            ),
            location=location or get_location(element=element, data_type=data_type),
        )

    def parse_sncl(self) -> Dict:
        return {
            "station": self.station,
            "network": self.network,
            "data_type": self.data_type,
            "element": self.element,
            "interval": self.interval,
        }

    @property
    def data_type(self) -> str:
        """Translates beginning of location code to data type"""
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
        return _check_predefined_element(channel=self.channel) or _get_element(
            channel=self.channel, location=self.location
        )

    @property
    def interval(self) -> str:
        """Translates beginning of channel to interval"""
        channel_start = self.channel[0]
        if channel_start == "B":
            return "tenhertz"
        elif channel_start == "L":
            return "second"
        elif channel_start == "U":
            return "minute"
        elif channel_start == "R":
            return "hour"
        elif channel_start == "P":
            return "day"
        raise ValueError(f"Unexcepted interval code: {channel_start}")


def get_channel(element: str, interval: str, data_type: str) -> str:
    return _check_predefined_channel(element=element, interval=interval) or (
        _get_channel_start(interval=interval)
        + _get_channel_end(element=element, data_type=data_type)
    )


def get_location(element: str, data_type: str) -> str:
    if len(data_type) == 2:
        return data_type
    return _get_location_start(data_type=data_type) + _get_location_end(element=element)


def _check_predefined_element(channel: str) -> Optional[str]:
    channel_end = channel[1:]
    if channel_end in CHANNEL_CONVERSIONS:
        return CHANNEL_CONVERSIONS[channel_end]
    return None


def _get_channel_start(interval: str) -> str:
    if interval == "tenhertz":
        return "B"
    if interval == "second":
        return "L"
    elif interval == "minute":
        return "U"
    elif interval == "hour":
        return "R"
    elif interval == "day":
        return "P"
    raise ValueError(f" Unexcepted interval: {interval}")


def _get_element(channel: str, location: str) -> str:
    """Translates channel/location to element"""
    element_start = channel[2]
    channel = channel
    channel_middle = channel[1]
    location_end = location[1]
    if channel_middle == "E":
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


def _check_predefined_channel(element: str, interval: str) -> Optional[str]:
    if element in ELEMENT_CONVERSIONS:
        return _get_channel_start(interval=interval) + ELEMENT_CONVERSIONS[element]
    elif len(element) == 3:
        return element
    # chan.loc format
    elif "." in element:
        channel = element.split(".")[0]
        return channel.strip()
    else:
        return None


def _get_channel_end(element: str, data_type: str) -> str:
    channel_middle = "F"
    if "_Volt" in element:
        channel_middle = "E"
    elif "_Bin" in element:
        channel_middle = "Y"
    elif "_Temp" in element:
        channel_middle = "K"
    channel_end = element.split("_")[0]
    if data_type == "variation":
        if channel_end == "H":
            channel_end = "U"
        elif channel_end == "E":
            channel_end = "V"
        elif channel_end == "Z":
            channel_end = "W"
    return channel_middle + channel_end


def _get_location_start(data_type: str) -> str:
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


def _get_location_end(element: str) -> str:
    """Translates element suffix to end of location code"""
    if "_Sat" in element:
        return "1"
    if "_Dist" in element:
        return "D"
    if "_SQ" in element:
        return "Q"
    if "_SV" in element:
        return "V"
    return "0"
