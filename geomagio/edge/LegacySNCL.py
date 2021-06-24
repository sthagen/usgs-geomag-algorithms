from typing import Optional

from .SNCL import SNCL, _get_location_start

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
    @classmethod
    def get_sncl(
        cls,
        data_type: str,
        element: str,
        interval: str,
        station: str,
        network: str = "NT",
        location: Optional[str] = None,
    ) -> "LegacySNCL":
        return LegacySNCL(
            station=station,
            network=network,
            channel=get_channel(element=element, interval=interval),
            location=location or get_location(element=element, data_type=data_type),
        )

    @property
    def element(self) -> str:
        return _check_predefined_element(channel=self.channel) or _get_element(
            channel=self.channel, location=self.location
        )

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


def get_channel(element: str, interval: str) -> str:
    return _check_predefined_channel(element=element, interval=interval) or (
        _get_channel_start(interval=interval) + _get_channel_end(element=element)
    )


def get_location(element: str, data_type: str) -> str:
    return _get_location_start(data_type=data_type) + _get_location_end(element=element)


def _check_predefined_element(channel: str) -> Optional[str]:
    channel_end = channel[1:]
    if channel_end in CHANNEL_CONVERSIONS:
        return CHANNEL_CONVERSIONS[channel_end]
    return None


def _get_channel_start(interval: str) -> str:
    if interval == "second":
        return "S"
    elif interval == "minute":
        return "M"
    elif interval == "hour":
        return "H"
    elif interval == "day":
        return "D"
    raise ValueError(f" Unexcepted interval: {interval}")


def _get_element(channel: str, location: str) -> str:
    """Translates channel/location to element"""
    element_start = channel[2]
    channel = channel
    channel_middle = channel[1]
    location_end = location[1]
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


def _get_channel_end(element: str) -> str:
    channel_middle = "V"
    if "_Volt" in element:
        channel_middle = "E"
    elif "_Bin" in element:
        channel_middle = "Y"
    elif "_Temp" in element:
        channel_middle = "K"
    elif element in ["F", "G"]:
        channel_middle = "S"
    channel_end = element.split("_")[0]
    return channel_middle + channel_end


def _get_location_end(element: str) -> str:
    """Translates element suffix to end of location code"""
    if "_Sat" in element:
        return "1"
    return "0"
