from typing import List

from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import Response

from ... import TimeseriesFactory
from ...algorithm import DbDtAlgorithm
from ...residual import (
    calculate,
    Reading,
    DECLINATION_TYPES,
    INCLINATION_TYPES,
    MARK_TYPES,
)
from .DataApiQuery import DataApiQuery
from .data import format_timeseries, get_data_factory, get_data_query, get_timeseries


router = APIRouter()


@router.get("/algorithms/dbdt/")
def get_dbdt(
    query: DataApiQuery = Depends(get_data_query),
    data_factory: TimeseriesFactory = Depends(get_data_factory),
) -> Response:
    dbdt = DbDtAlgorithm(period=query.sampling_period)
    # read data
    raw = get_timeseries(data_factory, query)
    # run dbdt
    timeseries = dbdt.process(raw)
    elements = [f"{element}_DT" for element in query.elements]
    # output response
    return format_timeseries(
        timeseries=timeseries, format=query.format, elements=elements
    )


@router.post("/algorithms/residual", response_model=Reading)
def calculate_residual(reading: Reading, adjust_reference: bool = True):
    missing_types = get_missing_measurement_types(reading=reading)
    if len(missing_types) != 0:
        missing_types = ", ".join(t.value for t in missing_types)
        raise HTTPException(
            status_code=400,
            detail=f"Missing {missing_types} measurements in input reading",
        )
    return calculate(reading=reading, adjust_reference=adjust_reference)


def get_missing_measurement_types(reading: Reading) -> List[str]:
    measurement_types = [m.measurement_type for m in reading.measurements]
    missing_types = []
    missing_types.extend(
        [type for type in DECLINATION_TYPES if type not in measurement_types]
    )
    missing_types.extend(
        [type for type in INCLINATION_TYPES if type not in measurement_types]
    )
    missing_types.extend([type for type in MARK_TYPES if type not in measurement_types])
    return missing_types
