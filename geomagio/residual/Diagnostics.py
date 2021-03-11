from typing import Optional

from .Measurement import Measurement
from pydantic import BaseModel


class Diagnostics(BaseModel):
    """Computed diagnostics during calculation.

    Attributes
    ----------
    inclination: Average of inclination measurements
    meridian: Calculated meridian value
    """

    inclination: float
    meridian: float
