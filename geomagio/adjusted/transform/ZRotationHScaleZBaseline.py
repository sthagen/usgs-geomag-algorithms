import numpy as np
import scipy.linalg as spl
from typing import List, Optional, Tuple

from .LeastSq import LeastSq


class ZRotationHscaleZbaseline(LeastSq):
    """Calculates affine using least squares, constrained to rotate about the Z axis,
    apply a uniform horizontal scaling, and apply a baseline shift for the Z axis."""

    def get_matrix(
        self,
        matrix: List[List[float]],
        absolutes: Optional[Tuple[List[float], List[float], List[float]]] = None,
        ordinates: Optional[Tuple[List[float], List[float], List[float]]] = None,
        weights: Optional[List[float]] = None,
    ) -> np.array:
        return [
            [matrix[0], matrix[1], 0.0, 0.0],
            [-matrix[1], matrix[0], 0.0, 0.0],
            [0.0, 0.0, 1.0, matrix[2]],
            [0.0, 0.0, 0.0, 1.0],
        ]

    def get_stacked_ordinates(
        self, ordinates: Tuple[List[float], List[float], List[float]]
    ) -> List[List[float]]:
        # (reduces degrees of freedom by 13:
        #  - 2 for making x,y independent of z;
        #  - 2 for making z independent of x,y;
        #  - 2 for not allowing shear in x,y;
        #  - 2 for not allowing translation in x,y;
        #  - 1 for not allowing scaling in z; and
        #  - 4 for the last row of zeros and a one)
        ord_stacked = np.zeros((3, len(ordinates[0]) * 3))
        ord_stacked[0, 0::3] = ordinates[0]
        ord_stacked[0, 1::3] = ordinates[1]
        ord_stacked[1, 0::3] = ordinates[1]
        ord_stacked[1, 1::3] = -ordinates[0]
        ord_stacked[2, 2::3] = 1.0
        return ord_stacked

    def get_stacked_values(
        self,
        absolutes: Tuple[List[float], List[float], List[float]],
        ordinates: Tuple[List[float], List[float], List[float]],
        weights: Optional[List[float]] = None,
    ) -> Tuple[List[float], List[float]]:
        # LHS, or dependent variables
        abs_stacked = self.get_stacked_absolutes(absolutes)
        # subtract z_o from z_a to force simple z translation
        abs_stacked[2::3] = absolutes[2] - ordinates[2]
        # RHS, or independent variables
        ord_stacked = self.get_stacked_ordinates(ordinates)
        return abs_stacked, ord_stacked
