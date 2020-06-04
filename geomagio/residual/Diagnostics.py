from typing import Optional

from pydantic import BaseModel


class Diagnostics(BaseModel):
    """Computed diagnostics during calculation.

    Attributes
    ----------
    meridian: calculated from declination measurements
    mean_mark: average mark angles from measurements
    magnetic_azimuh: after adjustment
    """

    meridian: float = None
    mean_mark: float = None
    magnetic_azimuth: float = None
