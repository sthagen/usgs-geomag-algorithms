import numpy as np
from typing import List, Optional, Tuple

from .LeastSq import LeastSq


class Rescale3D(LeastSq):
    """Calculates affine using using least squares, constrained to re-scale each axis"""

    def get_matrix(
        self,
        matrix: List[List[float]],
        absolutes: Optional[Tuple[List[float], List[float], List[float]]] = None,
        ordinates: Optional[Tuple[List[float], List[float], List[float]]] = None,
        weights: Optional[List[float]] = None,
    ) -> np.array:
        return [
            [matrix[0], 0.0, 0.0, 0.0],
            [0.0, matrix[1], 0.0, 0.0],
            [0.0, 0.0, matrix[2], 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]

    def get_stacked_ordinates(
        self, ordinates: Tuple[List[float], List[float], List[float]]
    ) -> List[List[float]]:
        # (reduces degrees of freedom by 13:
        #  - 2 for making x independent of y,z;
        #  - 2 for making y,z independent of x;
        #  - 1 for making y independent of z;
        #  - 1 for making z independent of y;
        #  - 3 for not translating xyz
        #  - 4 for the last row of zeros and a one)
        ord_stacked = np.zeros((3, len(ordinates[0]) * 3))
        ord_stacked[0, 0::3] = ordinates[0]
        ord_stacked[1, 1::3] = ordinates[1]
        ord_stacked[2, 2::3] = ordinates[2]
        return ord_stacked
