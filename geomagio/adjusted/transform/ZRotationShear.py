import numpy as np
import scipy.linalg as spl
from typing import List, Tuple

from .LeastSq import LeastSq


class ZRotationShear(LeastSq):
    def get_stacked_ordinates(self, ordinates):
        # (reduces degrees of freedom by 8:
        #  - 2 for making x,y independent of z;
        #  - 2 for making z independent of x,y
        #  - 4 for the last row of zeros and a one)
        ord_stacked = np.zeros((8, len(ordinates[0]) * 3))
        ord_stacked[0, 0::3] = ordinates[0]
        ord_stacked[1, 0::3] = ordinates[1]
        ord_stacked[2, 0::3] = 1.0
        ord_stacked[3, 1::3] = ordinates[0]
        ord_stacked[4, 1::3] = ordinates[1]
        ord_stacked[5, 1::3] = 1.0
        ord_stacked[6, 2::3] = ordinates[2]
        ord_stacked[7, 2::3] = 1.0
        return ord_stacked

    def format_matrix(self, matrix):
        return [
            [matrix[0], matrix[1], 0.0, matrix[2]],
            [matrix[3], matrix[4], 0.0, matrix[5]],
            [0.0, 0.0, matrix[6], matrix[7]],
            [0.0, 0.0, 0.0, 1.0],
        ]
