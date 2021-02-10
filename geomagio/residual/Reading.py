from typing import Dict, List, Optional, Tuple
from typing_extensions import Literal

import numpy as np
from obspy import Stream, UTCDateTime
from pydantic import BaseModel

from .. import TimeseriesUtility
from ..TimeseriesFactory import TimeseriesFactory
from .Absolute import Absolute
from .Measurement import Measurement, average_measurement
from .MeasurementType import MeasurementType


class Reading(BaseModel):
    """A collection of absolute measurements.

    Attributes
    ----------
    absolutes: absolutes computed from measurements.
    azimuth: azimuth angle to mark used for measurements, decimal degrees.
    hemisphere: 1 for northern hemisphere, -1 for southern hemisphere
    measurements: raw measurements used to compute absolutes.
    metadata: metadata used during absolute calculations.
    pier_correction: pier correction value, nT.
    scale_value: scale value in decimal degrees.
    """

    absolutes: List[Absolute] = []
    azimuth: float = 0
    hemisphere: Literal[-1, 1] = 1
    measurements: List[Measurement] = []
    metadata: Dict = {}
    pier_correction: float = 0
    scale_value: float = None

    def __getitem__(self, measurement_type: MeasurementType):
        """Provide access to measurements by type.

        Example: reading[MeasurementType.WEST_DOWN]
        """
        return [m for m in self.measurements if m.measurement_type == measurement_type]

    def get_absolute(
        self,
        element: str,
    ) -> Optional[Absolute]:
        for absolute in self.absolutes:
            if absolute.element == element:
                return absolute
        return None

    def load_ordinates(
        self,
        observatory: str,
        timeseries_factory: TimeseriesFactory,
        default_existing: bool = True,
    ):
        """Load ordinates from a timeseries factory.

        Parameters
        ----------
        observatory: the observatory to load.
        timeseries_factory: source of data.
        default_existing: keep existing values if data not found.
        """
        mean = average_measurement(self.measurements)
        data = timeseries_factory.get_timeseries(
            observatory=observatory,
            channels=("H", "E", "Z", "F"),
            interval="second",
            type="variation",
            starttime=mean.time,
            endtime=mean.endtime,
        )
        self.update_measurement_ordinates(data, default_existing)

    def update_measurement_ordinates(self, data: Stream, default_existing: bool = True):
        """Update ordinates.

        Parameters
        ----------
        data: source of data.
        default_existing: keep existing values if data not found.
        """
        for measurement in self.measurements:
            if not measurement.time:
                continue
            measurement.h = TimeseriesUtility.get_trace_value(
                traces=data.select(channel="H"),
                time=measurement.time,
                default=default_existing and measurement.h or None,
            )
            measurement.e = TimeseriesUtility.get_trace_value(
                traces=data.select(channel="E"),
                time=measurement.time,
                default=default_existing and measurement.e or None,
            )
            measurement.z = TimeseriesUtility.get_trace_value(
                traces=data.select(channel="Z"),
                time=measurement.time,
                default=default_existing and measurement.z or None,
            )
            measurement.f = TimeseriesUtility.get_trace_value(
                traces=data.select(channel="F"),
                time=measurement.time,
                default=default_existing and measurement.f or None,
            )

    @property
    def time(self) -> Optional[UTCDateTime]:
        h = self.get_absolute("H")
        if h:
            return h.endtime
        return None

    @property
    def valid(self) -> bool:
        """ensures that readings used in calculations have been marked as valid

        Attributes
        ----------
        readings: list containing valid and invalid readings
        """
        if (
            self.get_absolute("D").valid == True
            and self.get_absolute("H").valid == True
            and self.get_absolute("Z").valid == True
        ):
            return True


def get_absolutes(
    readings: List[Reading],
) -> Tuple[List[float], List[float], List[float]]:
    """Get H, D and Z absolutes"""
    h_abs = np.array([reading.get_absolute("H").absolute for reading in readings])
    d_abs = np.array([reading.get_absolute("D").absolute for reading in readings])
    z_abs = np.array([reading.get_absolute("Z").absolute for reading in readings])

    return (h_abs, d_abs, z_abs)


def get_absolutes_xyz(
    readings: List[Reading],
) -> Tuple[List[float], List[float], List[float]]:
    """Get X, Y and Z absolutes from H, D and Z baselines"""
    h_abs, d_abs, z_abs = get_absolutes(readings)
    # convert from cylindrical to Cartesian coordinates
    x_a = h_abs * np.cos(np.radians(d_abs))
    y_a = h_abs * np.sin(np.radians(d_abs))
    z_a = z_abs
    return (x_a, y_a, z_a)


def get_baselines(
    readings: List[Reading],
) -> Tuple[List[float], List[float], List[float]]:
    """Get H, D and Z baselines"""
    h_bas = np.array([reading.get_absolute("H").baseline for reading in readings])
    d_bas = np.array([reading.get_absolute("D").baseline for reading in readings])
    z_bas = np.array([reading.get_absolute("Z").baseline for reading in readings])
    return (h_bas, d_bas, z_bas)


def get_ordinates(
    readings: List[Reading],
) -> Tuple[List[float], List[float], List[float]]:
    """Calculates ordinates from absolutes and baselines"""
    h_abs, d_abs, z_abs = get_absolutes(readings)
    h_bas, d_bas, z_bas = get_baselines(readings)
    # recreate ordinate variometer measurements from absolutes and baselines
    h_ord = h_abs - h_bas
    d_ord = d_abs - d_bas
    z_ord = z_abs - z_bas
    e_ord = h_abs * np.radians(d_ord)
    h_ord = np.sqrt(h_ord ** 2 - e_ord ** 2)
    return (h_ord, e_ord, z_ord)
