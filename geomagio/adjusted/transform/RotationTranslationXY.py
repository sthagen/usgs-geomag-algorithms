import numpy as np
from typing import List, Tuple

from .SVD import SVD


class RotationTranslationXY(SVD):
    """Calculates affine using singular value decomposition,
    constrained to rotation and translation in XY(no scale or shear),
    and only translation in Z"""

    ndims = 2

    def get_rotation_matrix(self, U, Vh):
        return np.dot(Vh.T, np.dot(np.diag([1, np.linalg.det(np.dot(Vh.T, U.T))]), U.T))

    def format_matrix(self, R, T, weighted_absolutes, weighted_ordinates):
        return [
            [R[0, 0], R[0, 1], 0.0, T[0]],
            [R[1, 0], R[1, 1], 0.0, T[1]],
            [
                0.0,
                0.0,
                1.0,
                np.array(weighted_absolutes[self.ndims])
                - np.array(weighted_ordinates[self.ndims]),
            ],
            [0.0, 0.0, 0.0, 1.0],
        ]
