from typing import Optional

from pydantic import BaseModel


class Diagnostics(BaseModel):
    """Computed diagnostics during calculation.

    Attributes
    ----------
    meridian: claculated from declination measurements
    mean_mark: average mark angles from measurements
    magnetic_azimuh: after adjustment
    mark_azimuth: from metadata
    declination: from declination measurements
    inclination: from inclination measurements
    h_component: H baseline from calculations
    z_component: Z baseline from calculations
    """

    meridian: float = None
    mean_mark: float = None
    magnetic_azimuth: float = None
    mark_azimuth: float = None
    declination: float = None
    inclination: float = None
    h_component: float = None
    z_component: float = None
