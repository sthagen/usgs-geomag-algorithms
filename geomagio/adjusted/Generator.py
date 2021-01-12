import numpy as np
from pydantic import BaseModel
from typing import Type

from .GeneratorType import GeneratorType
from .Transform import Transform


class Generator(BaseModel):
    type: Type[Transform]
    memory: float = np.Inf
