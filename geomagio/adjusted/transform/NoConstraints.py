import numpy as np
import scipy.linalg as spl
from typing import List, Tuple

from .LeastSq import LeastSq

# TODO: DEFAULT IMPLEMENTATION FOR LEAST SQUARES?
# TODO: GET_STACKED_ORDINATES SO METHOD CAN BE SHARED
class NoConstraints(LeastSq):
    def calculate(
        self,
        ordinates: Tuple[List[float], List[float], List[float]],
        absolutes: Tuple[List[float], List[float], List[float]],
        weights: List[float],
    ) -> np.array:
        """Calculates affine with no constraints using least squares."""
        # LHS, or dependent variables
        #
        # [A[0,0], A[1,0], A[2,0], A[0,1], A[1,1], A[2,1], ...]
        abs_stacked = self.get_stacked_absolutes(absolutes)
        # RHS, or independent variables
        # (reduces degrees of freedom by 4:
        #  - 4 for the last row of zeros and a one)
        # [
        # [o[0,0], 0, 0, o[0,1], 0, 0, ...],
        # [0, o[1,0], 0, 0, o[1,1], 0, ...],
        # [0, 0, o[2,0], 0, 0, o[2,1], ...],
        # ...
        # ]
        ord_stacked = np.zeros((12, len(ordinates[0]) * 3))
        ord_stacked[0, 0::3] = ordinates[0]
        ord_stacked[1, 0::3] = ordinates[1]
        ord_stacked[2, 0::3] = ordinates[2]
        ord_stacked[3, 0::3] = 1.0
        ord_stacked[4, 1::3] = ordinates[0]
        ord_stacked[5, 1::3] = ordinates[1]
        ord_stacked[6, 1::3] = ordinates[2]
        ord_stacked[7, 1::3] = 1.0
        ord_stacked[8, 2::3] = ordinates[0]
        ord_stacked[9, 2::3] = ordinates[1]
        ord_stacked[10, 2::3] = ordinates[2]
        ord_stacked[11, 2::3] = 1.0

        ord_stacked = self.get_weighted_values(ord_stacked, weights)
        abs_stacked = self.get_weighted_values(abs_stacked, weights)

        # regression matrix M that minimizes L2 norm
        M_r, res, rank, sigma = spl.lstsq(ord_stacked.T, abs_stacked.T)
        if rank < 3:
            print("Poorly conditioned or singular matrix, returning NaNs")
            return np.nan * np.ones((4, 4))
        return np.array(
            [
                [M_r[0], M_r[1], M_r[2], M_r[3]],
                [M_r[4], M_r[5], M_r[6], M_r[7]],
                [M_r[8], M_r[9], M_r[10], M_r[11]],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )
