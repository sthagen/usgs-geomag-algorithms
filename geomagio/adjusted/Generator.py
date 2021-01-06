from obspy.core import UTCDateTime
from pydantic import BaseModel
from .. import pydantic_utcdatetime
from typing import List

from ..residual import Reading, WebAbsolutesFactory
from .Affine import Affine
from .AffineType import AffineType


class Generator(BaseModel):
    starttime: UTCDateTime
    endtime: UTCDateTime = UTCDateTime()
    readings: List[Reading] = None
    acausal: bool = False
    update_interval: int = 86400 * 7
    affines: List[Affine] = [
        Affine(type=AffineType.ROTATION_TRANSLATION_XY, memory=(86400 * 100)),
        Affine(type=AffineType.TRANSLATE_ORIGINS, memory=(86400 * 10)),
    ]
