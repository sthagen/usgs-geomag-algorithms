from geomagio.edge.SNCL import SNCL, get_channel, get_location


def test_data_type():
    """edge_test.SNCL_test.test_data_type()"""
    assert SNCL(station="BOU", channel="LFU", location="R0").data_type == "variation"
    assert SNCL(station="BOU", channel="LFU", location="A0").data_type == "adjusted"
    assert (
        SNCL(station="BOU", channel="LFU", location="Q0").data_type
        == "quasi-definitive"
    )
    assert SNCL(station="BOU", channel="LFU", location="D0").data_type == "definitive"


def test_element():
    """edge_test.SNCL_test.test_element()"""
    assert (
        SNCL(
            station="BOU",
            channel="UFD",
            location="R0",
        ).element
        == "D"
    )
    assert (
        SNCL(
            station="BOU",
            channel="UFU",
            location="R0",
        ).element
        == "U"
    )
    assert (
        SNCL(
            station="BOU",
            channel="UFF",
            location="R0",
        ).element
        == "F"
    )
    assert (
        SNCL(
            station="BOU",
            channel="UFH",
            location="R0",
        ).element
        == "H"
    )
    assert (
        SNCL(
            station="BOU",
            channel="UX4",
            location="R0",
        ).element
        == "Dst4"
    )
    assert (
        SNCL(
            station="BOU",
            channel="UX3",
            location="R0",
        ).element
        == "Dst3"
    )
    assert (
        SNCL(
            station="BOU",
            channel="UQE",
            location="R0",
        ).element
        == "E-E"
    )
    assert (
        SNCL(
            station="BOU",
            channel="UQN",
            location="R0",
        ).element
        == "E-N"
    )
    assert (
        SNCL(
            station="BOU",
            channel="BEU",
            location="R0",
        ).element
        == "U_Volt"
    )
    assert (
        SNCL(
            station="BOU",
            channel="BYU",
            location="R0",
        ).element
        == "U_Bin"
    )
    assert (
        SNCL(
            station="BOU",
            channel="UFU",
            location="R1",
        ).element
        == "U_Sat"
    )


def test_get_channel():
    """edge_test.SNCL_test.test_get_channel()"""
    assert (
        get_channel(element="U_Volt", interval="tenhertz", data_type="variation")
        == "BEU"
    )
    assert (
        get_channel(element="U_Bin", interval="tenhertz", data_type="variation")
        == "BYU"
    )
    assert get_channel(element="D", interval="second", data_type="variation") == "LFD"
    assert get_channel(element="D", interval="second", data_type="R0") == "LFD"
    assert get_channel(element="F", interval="minute", data_type="variation") == "UFF"
    assert get_channel(element="U", interval="hour", data_type="variation") == "RFU"
    assert get_channel(element="V", interval="hour", data_type="variation") == "RFV"
    assert get_channel(element="W", interval="hour", data_type="variation") == "RFW"
    assert get_channel(element="H", interval="hour", data_type="variation") == "RFU"
    assert get_channel(element="H", interval="hour", data_type="R0") == "RFU"
    assert get_channel(element="E", interval="hour", data_type="variation") == "RFV"
    assert get_channel(element="E", interval="hour", data_type="R0") == "RFV"
    assert get_channel(element="Z", interval="hour", data_type="variation") == "RFW"
    assert get_channel(element="Z", interval="hour", data_type="R0") == "RFW"
    # not variation data_type, test that H,Z is not converted to U,V
    assert get_channel(element="H", interval="hour", data_type="adjusted") == "RFH"
    assert get_channel(element="H", interval="hour", data_type="A0") == "RFH"
    assert get_channel(element="Z", interval="hour", data_type="adjusted") == "RFZ"
    assert get_channel(element="Z", interval="hour", data_type="A0") == "RFZ"
    assert get_channel(element="Dst4", interval="day", data_type="variation") == "PX4"
    assert (
        get_channel(element="Dst3", interval="minute", data_type="variation") == "UX3"
    )
    assert get_channel(element="E-E", interval="minute", data_type="variation") == "UQE"
    assert get_channel(element="E-N", interval="minute", data_type="variation") == "UQN"
    assert get_channel(element="UK1", interval="minute", data_type="variation") == "UK1"
    assert (
        get_channel(element="U_Dist", interval="minute", data_type="variation") == "UFU"
    )
    assert get_channel(element="U", interval="minute", data_type="RD") == "UFU"
    assert (
        get_channel(element="U_SQ", interval="minute", data_type="variation") == "UFU"
    )
    assert get_channel(element="U", interval="minute", data_type="RQ") == "UFU"
    assert (
        get_channel(element="U_SV", interval="minute", data_type="variation") == "UFU"
    )
    assert get_channel(element="U", interval="minute", data_type="RV") == "UFU"
    assert (
        get_channel(element="U_Dist", interval="minute", data_type="adjusted") == "UFU"
    )
    assert get_channel(element="U", interval="minute", data_type="AD") == "UFU"
    assert get_channel(element="U_SQ", interval="minute", data_type="adjusted") == "UFU"
    assert get_channel(element="U", interval="minute", data_type="AQ") == "UFU"
    assert get_channel(element="U_SV", interval="minute", data_type="adjusted") == "UFU"
    assert get_channel(element="U", interval="minute", data_type="AV") == "UFU"
    assert (
        get_channel(element="UK1.R0", interval="minute", data_type="variation") == "UK1"
    )


def test_get_location():
    """edge_test.SNCL_test.test_get_location()"""
    assert get_location(element="D", data_type="variation") == "R0"
    assert get_location(element="D", data_type="R0") == "R0"
    assert get_location(element="D", data_type="adjusted") == "A0"
    assert get_location(element="D", data_type="A0") == "A0"
    assert get_location(element="D", data_type="quasi-definitive") == "Q0"
    assert get_location(element="D", data_type="Q0") == "Q0"
    assert get_location(element="D", data_type="definitive") == "D0"
    assert get_location(element="D", data_type="D0") == "D0"
    assert get_location(element="D_Sat", data_type="variation") == "R1"
    assert get_location(element="D", data_type="R1") == "R1"
    assert get_location(element="D_Dist", data_type="variation") == "RD"
    assert get_location(element="D", data_type="RD") == "RD"
    assert get_location(element="D_SQ", data_type="variation") == "RQ"
    assert get_location(element="D", data_type="RQ") == "RQ"
    assert get_location(element="D_SV", data_type="variation") == "RV"
    assert get_location(element="D", data_type="RV") == "RV"


def test_get_sncl():
    """edge_test.SNCL_test.test_get_sncl()"""
    assert SNCL.get_sncl(
        station="BOU", data_type="variation", interval="second", element="U"
    ) == SNCL(station="BOU", network="NT", channel="LFU", location="R0")
    assert SNCL.get_sncl(
        station="BOU", data_type="variation", interval="second", element="H"
    ) == SNCL(station="BOU", network="NT", channel="LFU", location="R0")
    assert SNCL.get_sncl(
        station="BOU", data_type="R0", interval="second", element="H"
    ) == SNCL(station="BOU", network="NT", channel="LFU", location="R0")
    assert SNCL.get_sncl(
        station="BOU", data_type="A0", interval="second", element="H"
    ) == SNCL(station="BOU", network="NT", channel="LFH", location="A0")


def test_interval():
    """edge_test.SNCL_test.test_interval()"""
    assert (
        SNCL(
            station="BOU",
            channel="BEU",
            location="R0",
        ).interval
        == "tenhertz"
    )
    assert (
        SNCL(
            station="BOU",
            channel="LEU",
            location="R0",
        ).interval
        == "second"
    )
    assert (
        SNCL(
            station="BOU",
            channel="UEU",
            location="R0",
        ).interval
        == "minute"
    )
    assert (
        SNCL(
            station="BOU",
            channel="REU",
            location="R0",
        ).interval
        == "hour"
    )
    assert (
        SNCL(
            station="BOU",
            channel="PEU",
            location="R0",
        ).interval
        == "day"
    )


def test_parse_sncl():
    """edge_test.SNCL_test.test_parse_sncl()"""
    assert SNCL(station="BOU", channel="UFU", location="R0").parse_sncl() == {
        "station": "BOU",
        "network": "NT",
        "data_type": "variation",
        "element": "U",
        "interval": "minute",
    }
