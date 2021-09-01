from geomagio.edge.LegacySNCL import LegacySNCL, get_channel, get_location


def test_data_type():
    """edge_test.LegacySNCL_test.test_data_type()"""
    assert (
        LegacySNCL(station="BOU", channel="LFU", location="R0").data_type == "variation"
    )
    assert (
        LegacySNCL(station="BOU", channel="LFU", location="A0").data_type == "adjusted"
    )
    assert (
        LegacySNCL(station="BOU", channel="LFU", location="Q0").data_type
        == "quasi-definitive"
    )
    assert (
        LegacySNCL(station="BOU", channel="LFU", location="D0").data_type
        == "definitive"
    )


def test_element():
    """edge_test.LegacySNCL_test.test_element()"""
    assert (
        LegacySNCL(
            station="BOU",
            channel="MVD",
            location="R0",
        ).element
        == "D"
    )
    assert (
        LegacySNCL(
            station="BOU",
            channel="MVU",
            location="R0",
        ).element
        == "U"
    )
    assert (
        LegacySNCL(
            station="BOU",
            channel="MSF",
            location="R0",
        ).element
        == "F"
    )
    assert (
        LegacySNCL(
            station="BOU",
            channel="MVH",
            location="R0",
        ).element
        == "H"
    )
    assert (
        LegacySNCL(
            station="BOU",
            channel="MQE",
            location="R0",
        ).element
        == "E-E"
    )
    assert (
        LegacySNCL(
            station="BOU",
            channel="MQN",
            location="R0",
        ).element
        == "E-N"
    )
    assert (
        LegacySNCL(
            station="BOU",
            channel="MEH",
            location="R0",
        ).element
        == "H_Volt"
    )
    assert (
        LegacySNCL(
            station="BOU",
            channel="MYH",
            location="R0",
        ).element
        == "H_Bin"
    )
    assert (
        LegacySNCL(
            station="BOU",
            channel="MVH",
            location="R1",
        ).element
        == "H_Sat"
    )
    assert (
        LegacySNCL(
            station="BOU",
            channel="MDT",
            location="R0",
        ).element
        == "DIST"
    )
    assert (
        LegacySNCL(
            station="BOU",
            channel="MGD",
            location="R0",
        ).element
        == "DST"
    )


def test_get_channel():
    """edge_test.LegacySNCL_test.test_get_channel()"""
    assert get_channel(element="D", interval="second") == "SVD"
    assert get_channel(element="F", interval="minute") == "MSF"
    assert get_channel(element="H", interval="hour") == "HVH"
    assert get_channel(element="E-E", interval="day") == "DQE"
    assert get_channel(element="E-N", interval="minute") == "MQN"
    assert get_channel(element="SQ", interval="minute") == "MSQ"
    assert get_channel(element="SV", interval="minute") == "MSV"
    assert get_channel(element="UK1", interval="minute") == "UK1"
    assert get_channel(element="DIST", interval="minute") == "MDT"
    assert get_channel(element="DST", interval="minute") == "MGD"
    assert get_channel(element="UK1.R0", interval="minute") == "UK1"


def test_get_location():
    """edge_test.LegacySNCL_test.test_get_location()"""
    assert get_location(element="D", data_type="variation") == "R0"
    assert get_location(element="D", data_type="adjusted") == "A0"
    assert get_location(element="D", data_type="quasi-definitive") == "Q0"
    assert get_location(element="D", data_type="definitive") == "D0"
    assert get_location(element="D_Sat", data_type="variation") == "R1"
    assert get_location(element="D_Sat", data_type="adjusted") == "A1"
    assert get_location(element="D", data_type="R0") == "R0"
    assert get_location(element="D", data_type="A0") == "A0"
    assert get_location(element="D", data_type="Q0") == "Q0"
    assert get_location(element="D", data_type="D0") == "D0"
    assert get_location(element="D", data_type="R1") == "R1"
    assert get_location(element="D", data_type="A1") == "A1"


def test_get_sncl():
    """edge_test.LegacySNCL_test.test_get_sncl()"""
    assert LegacySNCL.get_sncl(
        station="BOU", data_type="variation", interval="second", element="H"
    ) == LegacySNCL(station="BOU", network="NT", channel="SVH", location="R0")
    assert LegacySNCL.get_sncl(
        station="BOU", data_type="R0", interval="second", element="H"
    ) == LegacySNCL(station="BOU", network="NT", channel="SVH", location="R0")


def test_interval():
    """edge_test.LegacySNCL_test.test_interval()"""
    assert (
        LegacySNCL(
            station="BOU",
            channel="SVH",
            location="R0",
            data_format="legacy",
        ).interval
        == "second"
    )
    assert (
        LegacySNCL(
            station="BOU",
            channel="MVH",
            location="R0",
            data_format="legacy",
        ).interval
        == "minute"
    )
    assert (
        LegacySNCL(
            station="BOU",
            channel="HVH",
            location="R0",
            data_format="legacy",
        ).interval
        == "hour"
    )
    assert (
        LegacySNCL(
            station="BOU",
            channel="DVH",
            location="R0",
            data_format="legacy",
        ).interval
        == "day"
    )


def test_parse_sncl():
    """edge_test.LegacySNCL_test.test_parse_sncl()"""
    assert LegacySNCL(station="BOU", channel="MVH", location="R0").parse_sncl() == {
        "station": "BOU",
        "network": "NT",
        "data_type": "variation",
        "element": "H",
        "interval": "minute",
    }
