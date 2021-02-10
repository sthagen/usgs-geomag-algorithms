import numpy as np
from typing import List, Tuple

from .SVD import SVD


class RotationTranslationXY(SVD):
    """Calculates affine using singular value decomposition,
    constrained to rotation and translation in XY(no scale or shear),
    and only translation in Z"""

    ndims: int = 2

    def get_matrix(
        self,
        R: List[List[float]],
        T: List[List[float]],
        weighted_absolutes: Tuple[List[float], List[float], List[float]],
        weighted_ordinates: Tuple[List[float], List[float], List[float]],
    ) -> np.array:
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

    def get_rotation_matrix(
        self, U: List[List[float]], Vh: List[List[float]]
    ) -> List[List[float]]:
        return np.dot(Vh.T, np.dot(np.diag([1, np.linalg.det(np.dot(Vh.T, U.T))]), U.T))
