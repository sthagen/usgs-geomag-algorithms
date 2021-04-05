import json

from obspy import UTCDateTime

from geomagio.adjusted import AdjustedMatrix, Metric
from geomagio.api.db import database, MetadataDatabaseFactory
from geomagio.api.ws.Observatory import OBSERVATORIES
from geomagio.metadata import Metadata, MetadataCategory
from geomagio.residual import SpreadsheetAbsolutesFactory, WebAbsolutesFactory


test_metadata = [
    Metadata(
        category=MetadataCategory.INSTRUMENT,
        created_by="test_metadata.py",
        network="NT",
        station="BDT",
        metadata={
            "type": "FGE",
            "channels": {
                # each channel maps to a list of components to calculate nT
                # TODO: calculate these lists based on "FGE" type
                "U": [{"channel": "U_Volt", "offset": 0, "scale": 313.2}],
                "V": [{"channel": "V_Volt", "offset": 0, "scale": 312.3}],
                "W": [{"channel": "W_Volt", "offset": 0, "scale": 312.0}],
            },
            "electronics": {
                "serial": "E0542",
                # these scale values are used to convert voltage
                "x-scale": 313.2,  # V/nT
                "y-scale": 312.3,  # V/nT
                "z-scale": 312.0,  # V/nT
                "temperature-scale": 0.01,  # V/K
            },
            "sensor": {
                "serial": "S0419",
                # these constants combine with instrument setting for offset
                "x-constant": 36958,  # nT/mA
                "y-constant": 36849,  # nT/mA
                "z-constant": 36811,  # nT/mA
            },
        },
    ),
    Metadata(
        category=MetadataCategory.INSTRUMENT,
        created_by="test_metadata.py",
        network="NT",
        station="NEW",
        metadata={
            "type": "Narod",
            "channels": {
                "U": [
                    {"channel": "U_Volt", "offset": 0, "scale": 100},
                    {"channel": "U_Bin", "offset": 0, "scale": 500},
                ],
                "V": [
                    {"channel": "V_Volt", "offset": 0, "scale": 100},
                    {"channel": "V_Bin", "offset": 0, "scale": 500},
                ],
                "W": [
                    {"channel": "W_Volt", "offset": 0, "scale": 100},
                    {"channel": "W_Bin", "offset": 0, "scale": 500},
                ],
            },
        },
    ),
    Metadata(
        category=MetadataCategory.INSTRUMENT,
        created_by="test_metadata.py",
        network="NT",
        station="LLO",
        metadata={
            "type": "Narod",
            "channels": {
                "U": [
                    {"channel": "U_Volt", "offset": 0, "scale": 100},
                    {"channel": "U_Bin", "offset": 0, "scale": 500},
                ],
                "V": [
                    {"channel": "V_Volt", "offset": 0, "scale": 100},
                    {"channel": "V_Bin", "offset": 0, "scale": 500},
                ],
                "W": [
                    {"channel": "W_Volt", "offset": 0, "scale": 100},
                    {"channel": "W_Bin", "offset": 0, "scale": 500},
                ],
            },
        },
    ),
]

# add observatories
for observatory in OBSERVATORIES:
    network = "NT"
    if observatory.agency == "USGS":
        network = "NT"
    # rest alphabetical by agency
    elif observatory.agency == "BGS":
        network = "GB"
    elif observatory.agency == "GSC":
        network = "C2"
    elif observatory.agency == "JMA":
        network = "JP"
    elif observatory.agency == "SANSA":
        network = "AF"
    test_metadata.append(
        Metadata(
            category=MetadataCategory.OBSERVATORY,
            created_by="test_metadata.py",
            network=network,
            station=observatory.id,
            metadata=observatory.dict(),
        )
    )

# get null readings
readings = WebAbsolutesFactory().get_readings(
    observatory="BOU",
    starttime=UTCDateTime("2020-01-01"),
    endtime=UTCDateTime("2020-01-07"),
)
# get residual reading
reading = SpreadsheetAbsolutesFactory().parse_spreadsheet(
    "etc/residual/DED-20140952332.xlsm"
)
readings.append(reading)

for reading in readings:
    json_string = reading.json()
    reading_dict = json.loads(json_string)
    try:
        reviewer = reading.metadata["reviewer"]
    except KeyError:
        reviewer = None
    test_metadata.append(
        Metadata(
            category=MetadataCategory.READING,
            created_by="test_metadata.py",
            network="NT",
            updated_by=reviewer,
            starttime=reading.time,
            endtime=reading.time,
            station=reading.metadata["station"],
            metadata=reading_dict,
            metadata_valid=reading.valid,
        )
    )


adjusted_matrix = AdjustedMatrix(
    matrix=[
        [0.9796103131299191, 0.20090702926851434, 0.0, -18.30071487449033],
        [-0.20090702926851361, 0.9796103131299198, 0.0, 406.9685381264491],
        [0.0, 0.0, 1.0, 708.4810320770974],
        [0.0, 0.0, 0.0, 1.0],
    ],
    pier_correction=-4.0,
    metrics=[
        Metric(element="X", absmean=0.5365143131738377, stddev=0.7246802312326883),
        Metric(element="Y", absmean=1.3338248076759354, stddev=2.1390294659087816),
        Metric(element="Z", absmean=0.7020521498941688, stddev=0.8991572596148847),
        Metric(element="dF", absmean=0.47978562187806045, stddev=0.5128104930705225),
    ],
)

test_metadata.append(
    Metadata(
        category="adjusted-matrix",
        station="FRD",
        network="NT",
        metadata=adjusted_matrix.dict(),
    )
)


async def load_test_metadata():
    await database.connect()
    for meta in test_metadata:
        await MetadataDatabaseFactory().create_metadata(meta)
    await database.disconnect()


if __name__ == "__main__":
    import asyncio

    asyncio.run(load_test_metadata())
