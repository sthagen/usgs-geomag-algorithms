from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import Response

from ... import TimeseriesFactory
from ...algorithm import DbDtAlgorithm
from ...residual import (
    calculate,
    Reading,
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
    try:
        return calculate(reading=reading, adjust_reference=adjust_reference)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
