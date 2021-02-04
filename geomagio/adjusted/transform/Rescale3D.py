import numpy as np
import scipy.linalg as spl
from typing import List, Tuple
from .LeastSq import LeastSq


class Rescale3D(LeastSq):
    """Calculates affine using using least squares, constrained to re-scale each axis"""

    def calculate(
        self,
        ordinates: Tuple[List[float], List[float], List[float]],
        absolutes: Tuple[List[float], List[float], List[float]],
        weights: List[float],
    ) -> np.array:
        abs_stacked = self.get_stacked_absolutes(absolutes=absolutes)
        # RHS, or independent variables
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

        abs_stacked = self.get_weighted_values(values=abs_stacked, weights=weights)
        ord_stacked = self.get_weighted_values(values=ord_stacked, weights=weights)

        # regression matrix M that minimizes L2 norm
        M_r, res, rank, sigma = spl.lstsq(ord_stacked.T, abs_stacked.T)
        if rank < 3:
            print("Poorly conditioned or singular matrix, returning NaNs")
            return np.nan * np.ones((4, 4))

        return [
            [M_r[0], 0.0, 0.0, 0.0],
            [0.0, M_r[1], 0.0, 0.0],
            [0.0, 0.0, M_r[2], 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
