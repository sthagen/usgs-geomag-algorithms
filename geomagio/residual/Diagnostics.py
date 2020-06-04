from typing import Optional

from .Measurement import Measurement
from pydantic import BaseModel


class Diagnostics(BaseModel):
    """Computed diagnostics during calculation.

    Attributes
    ----------
    inclination_measurement: Average of inclination measurements
    declination_measurement: Average of declination measurements
    mark_measurement: Average of mark measurements
    """

    inclination_measurement: Measurement
    declination_measurement: Measurement
    mark_measurement: Measurement
