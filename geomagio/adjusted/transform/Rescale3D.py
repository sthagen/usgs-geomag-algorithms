import numpy as np
import scipy.linalg as spl
from typing import List, Tuple
from .LeastSq import LeastSq


class Rescale3D(LeastSq):
    """Calculates affine using using least squares, constrained to re-scale each axis"""

    def get_stacked_ordinates(self, ordinates):
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

    def get_matrix(self, matrix, absolutes=None, ordinates=None, weights=None):
        return [
            [matrix[0], 0.0, 0.0, 0.0],
            [0.0, matrix[1], 0.0, 0.0],
            [0.0, 0.0, matrix[2], 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
