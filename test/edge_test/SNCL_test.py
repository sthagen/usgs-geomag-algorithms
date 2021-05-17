from geomagio.edge import SNCL


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


def test_get_sncl():
    """edge_test.SNCL_test.test_get_sncl()"""
    assert SNCL().get_sncl(
        station="BOU", data_type="variation", interval="second", element="U"
    ) == SNCL(station="BOU", network="NT", channel="LFU", location="R0")


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
