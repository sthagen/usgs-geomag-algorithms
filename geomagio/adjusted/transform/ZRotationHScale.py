import numpy as np
from typing import List, Optional, Tuple

from .LeastSq import LeastSq


class ZRotationHscale(LeastSq):
    """Calculates affine using least squares, constrained to rotate about the Z axis
    and apply uniform horizontal scaling."""

    def get_matrix(
        self,
        matrix: List[List[float]],
        absolutes: Optional[Tuple[List[float], List[float], List[float]]] = None,
        ordinates: Optional[Tuple[List[float], List[float], List[float]]] = None,
        weights: Optional[List[float]] = None,
    ) -> np.array:
        return [
            [matrix[0], matrix[1], 0.0, matrix[2]],
            [-matrix[1], matrix[0], 0.0, matrix[3]],
            [0.0, 0.0, matrix[4], matrix[5]],
            [0.0, 0.0, 0.0, 1.0],
        ]

    def get_stacked_ordinates(
        self, ordinates: Tuple[List[float], List[float], List[float]]
    ) -> List[List[float]]:
        # (reduces degrees of freedom by 10:
        #  - 2 for making x,y independent of z;
        #  - 2 for making z independent of x,y
        #  - 2 for not allowing shear in x,y; and
        #  - 4 for the last row of zeros and a one)
        ord_stacked = np.zeros((6, len(ordinates[0]) * 3))
        ord_stacked[0, 0::3] = ordinates[0]
        ord_stacked[0, 1::3] = ordinates[1]
        ord_stacked[1, 0::3] = ordinates[1]
        ord_stacked[1, 1::3] = -ordinates[0]
        ord_stacked[2, 0::3] = 1.0
        ord_stacked[3, 1::3] = 1.0
        ord_stacked[4, 2::3] = ordinates[2]
        ord_stacked[5, 2::3] = 1.0
        return ord_stacked
