from obspy.core import UTCDateTime
from pydantic import BaseModel
from .. import pydantic_utcdatetime
from typing import List, Any, Optional

from .Generator import Generator
from .GeneratorType import GeneratorType


class Affine(BaseModel):
    observatory: str = None
    starttime: UTCDateTime = UTCDateTime() - (86400 * 7)
    endtime: UTCDateTime = UTCDateTime()
    acausal: bool = False
    update_interval: Optional[int] = 86400 * 7
    generators: List[Generator] = [
        Generator(type=GeneratorType.ROTATION_TRANSLATION_XY, memory=(86400 * 100)),
        Generator(type=GeneratorType.TRANSLATE_ORIGINS, memory=(86400 * 10)),
    ]
    pier_correction: float = None
    # TODO: specify array type with fixed shape
    matrix: Any = None
