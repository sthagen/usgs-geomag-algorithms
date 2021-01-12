from obspy.core import UTCDateTime
from pydantic import BaseModel
from .. import pydantic_utcdatetime
from typing import List, Any, Optional

from .Generator import Generator
from .GeneratorType import GeneratorType
from .Transform import Transform, TranslateOrigins, RotationTranslationXY


def create_states(matrices: List[Any], pier_correction: float) -> List[dict]:
    if matrices is None:
        return []
    states = []
    for matrix in matrices:
        data = {"PC": pier_correction}
        length = len(matrix[0, :])
        for i in range(0, length):
            for j in range(0, length):
                key = "M" + str(i + 1) + str(j + 1)
                data[key] = matrix[i, j]
        states.append(data)
    return states


class Affine(BaseModel):
    observatory: str = None
    starttime: UTCDateTime = UTCDateTime() - (86400 * 7)
    endtime: UTCDateTime = UTCDateTime()
    acausal: bool = False
    update_interval: Optional[int] = 86400 * 7
    generators: List[Generator] = [
        Generator(type=RotationTranslationXY, memory=(86400 * 100)),
        Generator(type=TranslateOrigins, memory=(86400 * 10)),
    ]
    pier_correction: float = None
    # TODO: specify array type with fixed shape
    matrices: Any = None
    states: List[dict] = create_states(matrices, pier_correction)
