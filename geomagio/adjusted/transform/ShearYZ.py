import numpy as np
import scipy.linalg as spl
from typing import List, Tuple

from .LeastSq import LeastSq


class ShearYZ(LeastSq):
    """Calculates affine using least squares, constrained to shear y and z, but not x."""

    def get_stacked_ordinates(self, ordinates):
        # (reduces degrees of freedom by 13:
        #  - 2 for making x independent of y,z;
        #  - 1 for making y independent of z;
        #  - 3 for not scaling each axis
        #  - 4 for the last row of zeros and a one)
        ord_stacked = np.zeros((3, len(ordinates[0]) * 3))
        ord_stacked[0, 0::3] = 1.0
        ord_stacked[1, 0::3] = ordinates[0]
        ord_stacked[1, 1::3] = 1.0
        ord_stacked[2, 0::3] = ordinates[0]
        ord_stacked[2, 1::3] = ordinates[1]
        ord_stacked[2, 2::3] = 1.0
        return ord_stacked

    def get_matrix(self, matrix, absolutes=None, ordinates=None, weights=None):
        return [
            [1.0, 0.0, 0.0, 0.0],
            [matrix[0], 1.0, 0.0, 0.0],
            [matrix[1], matrix[2], 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
