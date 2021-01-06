import numpy as np
from pydantic import BaseModel

from . import AffineType


class Affine(BaseModel):
    type: AffineType
    memory: float = np.Inf
