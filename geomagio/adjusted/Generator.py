import numpy as np
from pydantic import BaseModel

from .GeneratorType import GeneratorType


class Generator(BaseModel):
    type: GeneratorType
    memory: float = np.Inf
