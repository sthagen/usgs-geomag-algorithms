from geomagio.edge import SNCL


def test_data_type():
    assert SNCL(station="BOU", channel="LFU", location="R0").data_type == "variation"
    assert SNCL(station="BOU", channel="LFU", location="A0").data_type == "adjusted"
    assert (
        SNCL(station="BOU", channel="LFU", location="Q0").data_type
        == "quasi-definitive"
    )
    assert SNCL(station="BOU", channel="LFU", location="D0").data_type == "definitive"


def test_interval():
    # miniseed format
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
    # legacy format
    assert (
        SNCL(
            station="BOU",
            channel="SVH",
            location="R0",
            data_format="legacy",
        ).interval
        == "second"
    )
    assert (
        SNCL(
            station="BOU",
            channel="MVH",
            location="R0",
            data_format="legacy",
        ).interval
        == "minute"
    )
    assert (
        SNCL(
            station="BOU",
            channel="HVH",
            location="R0",
            data_format="legacy",
        ).interval
        == "hour"
    )
    assert (
        SNCL(
            station="BOU",
            channel="DVH",
            location="R0",
            data_format="legacy",
        ).interval
        == "day"
    )


def test_element():
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

    assert (
        SNCL(
            station="BOU",
            channel="MVD",
            location="R0",
            data_format="legacy",
        ).element
        == "D"
    )
    assert (
        SNCL(
            station="BOU",
            channel="MVU",
            location="R0",
            data_format="legacy",
        ).element
        == "U"
    )
    assert (
        SNCL(
            station="BOU",
            channel="MSF",
            location="R0",
            data_format="legacy",
        ).element
        == "F"
    )
    assert (
        SNCL(
            station="BOU",
            channel="MVH",
            location="R0",
            data_format="legacy",
        ).element
        == "H"
    )
    assert (
        SNCL(
            station="BOU",
            channel="MX4",
            location="R0",
            data_format="legacy",
        ).element
        == "Dst4"
    )
    assert (
        SNCL(
            station="BOU",
            channel="MX3",
            location="R0",
            data_format="legacy",
        ).element
        == "Dst3"
    )
    assert (
        SNCL(
            station="BOU",
            channel="MQE",
            location="R0",
            data_format="legacy",
        ).element
        == "E-E"
    )
    assert (
        SNCL(
            station="BOU",
            channel="MQN",
            location="R0",
            data_format="legacy",
        ).element
        == "E-N"
    )
    assert (
        SNCL(
            station="BOU",
            channel="MEH",
            location="R0",
            data_format="legacy",
        ).element
        == "H_Volt"
    )
    assert (
        SNCL(
            station="BOU",
            channel="MYH",
            location="R0",
            data_format="legacy",
        ).element
        == "H_Bin"
    )
    assert (
        SNCL(
            station="BOU",
            channel="MVH",
            location="R1",
            data_format="legacy",
        ).element
        == "H_Sat"
    )
    assert (
        SNCL(
            station="BOU",
            channel="MVH",
            location="RD",
            data_format="legacy",
        ).element
        == "H_Dist"
    )
    assert (
        SNCL(
            station="BOU",
            channel="MVH",
            location="RQ",
            data_format="legacy",
        ).element
        == "H_SQ"
    )
    assert (
        SNCL(
            station="BOU",
            channel="MVH",
            location="RV",
            data_format="legacy",
        ).element
        == "H_SV"
    )
    assert (
        SNCL(
            station="BOU",
            channel="MDT",
            location="RV",
            data_format="legacy",
        ).element
        == "DIST"
    )
    assert (
        SNCL(
            station="BOU",
            channel="MGD",
            location="RV",
            data_format="legacy",
        ).element
        == "DST"
    )
