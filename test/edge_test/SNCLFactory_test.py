from geomagio.edge import SNCL, SNCLFactory


def test_get_sncl():
    assert (
        SNCLFactory(data_format="miniseed").get_sncl(
            station="BOU",
            data_type="variation",
            element="UFU",
            interval="minute",
        )
        == SNCL(station="BOU", network="NT", channel="UFU", location="R0")
    )
    assert (
        SNCLFactory(data_format="legacy").get_sncl(
            station="BOU",
            data_type="variation",
            element="MVH",
            interval="minute",
        )
        == SNCL(station="BOU", network="NT", channel="MVH", location="R0")
    )


def test_get_channel():
    # test miniseed format
    factory = SNCLFactory(data_format="miniseed")
    assert factory.get_channel(element="D", interval="minute") == "UFD"
    assert factory.get_channel(element="F", interval="minute") == "UFF"
    assert factory.get_channel(element="H", interval="minute") == "UFH"
    assert factory.get_channel(element="Dst4", interval="minute") == "UX4"
    assert factory.get_channel(element="Dst3", interval="minute") == "UX3"
    assert factory.get_channel(element="E-E", interval="minute") == "UQE"
    assert factory.get_channel(element="E-N", interval="minute") == "UQN"
    assert factory.get_channel(element="SQ", interval="minute") == "USQ"
    assert factory.get_channel(element="SV", interval="minute") == "USV"
    assert factory.get_channel(element="UK1", interval="minute") == "UK1"
    assert factory.get_channel(element="UK2", interval="minute") == "UK2"
    assert factory.get_channel(element="UK3", interval="minute") == "UK3"
    assert factory.get_channel(element="UK4", interval="minute") == "UK4"
    assert factory.get_channel(element="DIST", interval="minute") == "UDT"
    assert factory.get_channel(element="DST", interval="minute") == "UGD"
    assert factory.get_channel(element="U_Dist", interval="minute") == "UFU"
    assert factory.get_channel(element="UK1.R0", interval="minute") == "UK1"

    # test legacy format
    factory = SNCLFactory(data_format="legacy")
    assert factory.get_channel(element="D", interval="minute") == "MVD"
    assert factory.get_channel(element="F", interval="minute") == "MSF"
    assert factory.get_channel(element="H", interval="minute") == "MVH"
    assert factory.get_channel(element="Dst4", interval="minute") == "MX4"
    assert factory.get_channel(element="Dst3", interval="minute") == "MX3"
    assert factory.get_channel(element="E-E", interval="minute") == "MQE"
    assert factory.get_channel(element="E-N", interval="minute") == "MQN"
    assert factory.get_channel(element="SQ", interval="minute") == "MSQ"
    assert factory.get_channel(element="SV", interval="minute") == "MSV"
    assert factory.get_channel(element="UK1", interval="minute") == "UK1"
    assert factory.get_channel(element="UK2", interval="minute") == "UK2"
    assert factory.get_channel(element="UK3", interval="minute") == "UK3"
    assert factory.get_channel(element="UK4", interval="minute") == "UK4"
    assert factory.get_channel(element="DIST", interval="minute") == "MDT"
    assert factory.get_channel(element="DST", interval="minute") == "MGD"
    assert factory.get_channel(element="H_Dist", interval="minute") == "MVH"
    assert factory.get_channel(element="UK1.R0", interval="minute") == "UK1"


def test_get_location():
    factory = SNCLFactory(data_format="miniseed")
    assert factory.get_location(element="D", data_type="variation") == "R0"
    assert factory.get_location(element="D", data_type="adjusted") == "A0"
    assert factory.get_location(element="D", data_type="quasi-definitive") == "Q0"
    assert factory.get_location(element="D", data_type="definitive") == "D0"
    assert factory.get_location(element="D_Sat", data_type="variation") == "R1"
    assert factory.get_location(element="D_Dist", data_type="variation") == "RD"
    assert factory.get_location(element="D_SQ", data_type="variation") == "RQ"
    assert factory.get_location(element="D_SV", data_type="variation") == "RV"
