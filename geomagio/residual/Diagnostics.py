from typing import Optional

from pydantic import BaseModel


class Diagnostics(BaseModel):
    """Computed diagnostics during calculation.

    Attributes
    ----------
    inclination: Average of inclination measurements
    meridian: Calculated meridian value
    """

    inclination: float
    meridian: Optional[float] = None
